#include <Arduino.h>
#include <MCP45HVX1.h>
#include <PAC1720.h>
#include "si5351.h"
#include "Wire.h"
#include <avr/sleep.h>

#define DCDC_ENABLE 2
#define LEDPIN  (13)
PAC1720 Sense; //Instatiate sensor

unsigned long Period = 1000; //Wait 1 second between prints
uint8_t ResVals[2] = {27, 27}; //Mapping of resistor values [mOhms]

MCP45HVX1 digiPot(0x3C);
Si5351 si5351;

void setup()
{
  bool i2c_found;
  pinMode(DCDC_ENABLE, OUTPUT);
  digitalWrite(DCDC_ENABLE, LOW);

  Serial.begin(57600);
  i2c_found = si5351.init(SI5351_CRYSTAL_LOAD_8PF, 0, 0);
  if(!i2c_found)
  {
    Serial.println("Device not found on I2C bus!");
  }

  Sense.begin(); //Basic setup
  while(!Serial); //Wait for serial to start

  // Set CLK0 to output 14 MHz
  digiPot.begin();

  set_frequency(180e3);
  set_DC_voltage(10);
  digitalWrite(DCDC_ENABLE, HIGH);
  delay(1000);
  Serial.println("Input voltage");
  Serial.println(Sense.GetSenseVoltage(1));

  Serial.println("\n----- Wiper Register ----");
  Serial.print("readWiper: ");
  Serial.println(digiPot.readWiper());

  delay(500);
}

void loop()
{
  float Bus[2] = {0}; //Setup array for bus voltages
  float Current[2] = {0}; //Setup array for current values

  // String Data;
  char Data[100]; //String to concatonate data into for single print

  for(int i = 0; i < 2; i++) {
    Bus[i] = Sense.GetBusVoltage(i); //Get bus voltage
    Current[i] = Sense.GetSenseVoltage(i); //Get sensing voltage
    // Current[i] = Sense.GetCurrent(i, ResVals[i]); //Get calculated current
  }
  sprintf(Data, "Vbus1 = %dmV\tVsense1 = %+dmA\tVbus2 = %dmV\tVsense2 = %+dmA\n", int(Bus[0]*1000.0), int(Current[0]/ResVals[0]*1000), int(Bus[1]*1000.0), int(Current[1]/ResVals[1]*1000)); //Format string for sufficient resolution for each value and +/- indication for clarity on current 
  Serial.print(Data); //Print out preformatted data string
  // Serial.println(Current[0], 8); //DEBUG!
  delay(Period);
  
  Sleep();
  

}

int set_frequency(unsigned long long target_f) {
  si5351.set_freq(100 * target_f, SI5351_CLK0);
  si5351.update_status();
}

int set_DC_voltage(int target_v) {
  float target_r = ((target_v / 0.9) - 1) * 3.9e3 - 100;

  digiPot.writeWiper(round(target_r / 392));

  Serial.println("\n----- Wiper Register ----");
  Serial.print("readWiper: ");
  Serial.println(digiPot.readWiper());

  return round(target_r / 392);
}

// 外部割り込みの結果呼び出される関数
void wakeUpNow()
{
  ; // 何もなし
}

void Sleep()
{
  // スリープ中の消費電力を最小限に抑えるために、
  //  i) 出力ピンは電流を供給なし
  // ii) 入力ピンは一定
  // にする。
  // i) ii) を実現する簡単な方法は、内部プルアップ抵抗を有効にすること。
  for( int i = 0; i < 20; i++ )
  {
    pinMode(i, INPUT_PULLUP);
  }

  // LEDピンのセットアップ
  pinMode( LEDPIN, OUTPUT );
  digitalWrite( LEDPIN, LOW );


  // ① アナログ・デジタル・コンバータ機能を無効にする（少しでも電力消費を抑えるため）
  byte adcsra_old = ADCSRA; // ADC Control と Register Aの設定値の以前の値を保持。
  ADCSRA = 0;   // アナログ・デジタル・コンバータ機能の無効にする。

  // ② スリープモードを設定する（②⑤⑧でセット）
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);

  // ③ 割り込み機能を無効にする（④⑤の処理を確実に実行するため）
  noInterrupts(); // cli()でも同じ

  // ④ 電圧降下検出機能を無効にする（少しでも電力消費を抑えるため）
  sleep_bod_disable();

  // ⑤ スリープ機能を有効にする（②⑤⑧でセット）
  sleep_enable();

  // ⑥ 割り込み機能を有効にする（④⑤の処理を実行したので元に戻す）
  interrupts(); // sei()でも同じ

  // ⑦ 外部割り込み条件を設定する（Wakeするための外部割り込み条件の割込設定）
  attachInterrupt(0,wakeUpNow, LOW);  // INT0端子(２番ピン)の立ち下がりで割り込み発生。wakeUpNow関数が呼ばれる。

  // ⑧ スリープ実行（②⑤⑧でセット）
  sleep_cpu();

  // （⑧によってスリープに移行する。⑦で設定した外部割り込みでWakeし、⑨の処理が実施される）

  // ⑨ スリープ機能を無効にする（⑦で設定した外部割り込みでWakeしたので、スリープを無効にする）
  sleep_disable();

  // ⑩ 外部割り込み条件の設定を解除する（Wakeしたので）
  detachInterrupt(0);

  // ⑪ アナログ・デジタル・コンバータ機能を有効にする（Wakeしたので）
  ADCSRA = adcsra_old;
}

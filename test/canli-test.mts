import { loggerOlustur, kisiselVeriyiTemizle } from '../typescript/logger'

const API = process.env.FIREBASE_API_KEY!
const PID = process.env.FIREBASE_PROJECT_ID!

let gecti = 0, kaldi = 0
const dogrula = (ad: string, kosul: boolean, ek = '') => {
  console.log(`  ${kosul ? '✓' : '✗'} ${ad}${ek ? ' — ' + ek : ''}`)
  kosul ? gecti++ : kaldi++
}

console.log('\nBulut logger canlı testi\n')

console.log('1) Kişisel veri temizleme')
const kirli = { veli_telefon: '05321234567', not: 'veli ahmet@mail.com aradı, TC 12345678901', ad: 'Ali' }
const temiz = kisiselVeriyiTemizle(kirli) as Record<string, string>
dogrula('telefon alanı gizlendi', temiz.veli_telefon === '<gizlendi>', temiz.veli_telefon)
dogrula('metin içindeki e-posta maskelendi', temiz.not.includes('<eposta>'), temiz.not)
dogrula('metin içindeki kimlik no maskelendi', temiz.not.includes('<kimlik>'), temiz.not)

console.log('\n2) Firestore’a gerçek yazma')
const logger = loggerOlustur({
  uygulamaAdi: 'cloud-logger-selftest',
  surum: '1.0.0',
  firebaseProjeId: PID,
  firebaseApiKey: API,
  ortam: 'test'
})
const hataYazildi = await logger.hata(new Error('Canlı doğrulama hatası'), { kaynak: 'canli-test' })
dogrula('ERROR kaydı crash_logs’a yazıldı (HTTP ok)', hataYazildi === true)

console.log('\n3) Kota koruması')
const kotali = loggerOlustur({
  uygulamaAdi: 'kota-testi', firebaseProjeId: PID, firebaseApiKey: API,
  bilgiOrneklemeOrani: 0, oturumBasinaAzami: 2
})
const b1 = await kotali.info('gonderilmemeli')
dogrula('INFO örnekleme 0 iken gönderilmiyor', b1 === false)
const e1 = await kotali.hata('bir')
const e2 = await kotali.hata('iki')
const e3 = await kotali.hata('uc — sinir asildi')
dogrula('oturum sınırı sonrası gönderim duruyor', e1 && e2 && e3 === false, `${e1}/${e2}/${e3}`)

console.log('\n4) Çökmezlik')
const bozuk = loggerOlustur({ uygulamaAdi: 'x', firebaseProjeId: 'olmayan-proje', firebaseApiKey: 'gecersiz' })
const sonuc = await bozuk.hata('ulasilamaz uc nokta')
dogrula('geçersiz yapılandırmada hata fırlatmıyor, false dönüyor', sonuc === false)

console.log(`\nSonuç: ${gecti} başarılı, ${kaldi} başarısız\n`)
process.exit(kaldi ? 1 : 0)

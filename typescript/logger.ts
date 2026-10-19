/**
 * Created by 11Hopem
 * Copyright (c) 2026 11hopem. All rights reserved.
 *
 * Tarayıcıdan Firebase'e log yazan istemci.
 *
 * Neden Firestore REST: Cloud Logging ve Error Reporting uçları OAuth2 ister;
 * tarayıcıda servis hesabı tutulamayacağı için o uçlara yapılan istekler
 * sessizce başarısız olur. Firestore REST, public web apiKey ile yazmaya
 * izin verir ve kuralları yalnızca yazmaya açıktır.
 */

export type LogSeviyesi = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'

export interface LoggerAyarlari {
  uygulamaAdi: string
  surum?: string
  firebaseProjeId: string
  firebaseApiKey: string
  ortam?: string
  /** INFO/DEBUG kayıtlarının gönderilme oranı (0-1). Ücretsiz kota için. */
  bilgiOrneklemeOrani?: number
  /** Oturum başına gönderilecek azami kayıt. Döngüye giren hata kotayı yakmasın. */
  oturumBasinaAzami?: number
}

const AGIR_SEVIYELER: LogSeviyesi[] = ['ERROR', 'CRITICAL']

const GIZLENECEK_ANAHTARLAR = [
  'telefon', 'phone', 'gsm', 'eposta', 'email', 'mail', 'tc', 'tckn', 'kimlik',
  'veli', 'parola', 'password', 'sifre', 'token', 'secret', 'apikey', 'adres', 'address'
]

const DESENLER: [RegExp, string][] = [
  [/\b[\w.+-]+@[\w-]+\.[\w.]+\b/g, '<eposta>'],
  [/\b0?5\d{9}\b/g, '<telefon>'],
  [/\b\d{11}\b/g, '<kimlik>'],
  [/\b(?:\d[ -]?){13,19}\b/g, '<kart>']
]

export function kisiselVeriyiTemizle(deger: unknown, anahtar = ''): unknown {
  if (GIZLENECEK_ANAHTARLAR.some((a) => anahtar.toLowerCase().includes(a))) return '<gizlendi>'
  if (typeof deger === 'string') {
    let temiz = deger
    for (const [kalip, yerine] of DESENLER) temiz = temiz.replace(kalip, yerine)
    return temiz.length > 2000 ? temiz.slice(0, 2000) + '…' : temiz
  }
  if (Array.isArray(deger)) return deger.slice(0, 20).map((d) => kisiselVeriyiTemizle(d))
  if (deger && typeof deger === 'object') {
    const cikti: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(deger as Record<string, unknown>).slice(0, 30)) {
      cikti[k] = kisiselVeriyiTemizle(v, k)
    }
    return cikti
  }
  return deger
}

function firestoreDegeri(deger: unknown): Record<string, unknown> {
  if (deger === null || deger === undefined) return { nullValue: null }
  if (typeof deger === 'number') return { doubleValue: deger }
  if (typeof deger === 'boolean') return { booleanValue: deger }
  if (typeof deger === 'object') return { stringValue: JSON.stringify(deger).slice(0, 4000) }
  return { stringValue: String(deger).slice(0, 4000) }
}

export class BulutLogger {
  private ayarlar: Required<LoggerAyarlari>
  private gonderilen = 0

  constructor(ayarlar: LoggerAyarlari) {
    this.ayarlar = {
      surum: '0.0.0',
      ortam: 'production',
      bilgiOrneklemeOrani: 0.05,
      oturumBasinaAzami: 50,
      ...ayarlar
    }
  }

  private gonderilmeli(seviye: LogSeviyesi): boolean {
    if (this.gonderilen >= this.ayarlar.oturumBasinaAzami) return false
    if (AGIR_SEVIYELER.includes(seviye) || seviye === 'WARNING') return true
    return Math.random() < this.ayarlar.bilgiOrneklemeOrani
  }

  private koleksiyon(seviye: LogSeviyesi): string {
    return AGIR_SEVIYELER.includes(seviye) ? 'crash_logs' : 'app_logs'
  }

  /**
   * Kaydı gönderir. Dönen söz hiçbir zaman reddetmez; uygulama tarafında
   * beklenmesi gerekmez (fire-and-forget), testlerde beklenebilsin diye döner.
   */
  kayit(seviye: LogSeviyesi, mesaj: string, baglam: Record<string, unknown> = {}): Promise<boolean> {
    try {
      if (!this.gonderilmeli(seviye)) return Promise.resolve(false)
      this.gonderilen++

      const alanlar: Record<string, unknown> = {
        appName: firestoreDegeri(this.ayarlar.uygulamaAdi),
        appVersion: firestoreDegeri(this.ayarlar.surum),
        projectId: firestoreDegeri(this.ayarlar.firebaseProjeId),
        env: firestoreDegeri(this.ayarlar.ortam),
        level: firestoreDegeri(seviye),
        event: firestoreDegeri(AGIR_SEVIYELER.includes(seviye) ? 'UNHANDLED_ERROR' : 'APP_EVENT'),
        message: firestoreDegeri(kisiselVeriyiTemizle(mesaj)),
        context: firestoreDegeri(kisiselVeriyiTemizle(baglam)),
        timestamp: firestoreDegeri(new Date().toISOString())
      }

      if (typeof window !== 'undefined') {
        alanlar.url = firestoreDegeri(kisiselVeriyiTemizle(window.location?.href ?? ''))
        alanlar.userAgent = firestoreDegeri(navigator?.userAgent ?? '')
      }

      const adres =
        `https://firestore.googleapis.com/v1/projects/${this.ayarlar.firebaseProjeId}` +
        `/databases/(default)/documents/${this.koleksiyon(seviye)}?key=${this.ayarlar.firebaseApiKey}`

      return fetch(adres, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields: alanlar }),
        keepalive: true
      })
        .then((y) => y.ok)
        .catch(() => false)
    } catch {
      /* loglama hiçbir koşulda uygulamayı düşürmez */
      return Promise.resolve(false)
    }
  }

  debug(m: string, b?: Record<string, unknown>) { return this.kayit('DEBUG', m, b) }
  info(m: string, b?: Record<string, unknown>) { return this.kayit('INFO', m, b) }
  uyari(m: string, b?: Record<string, unknown>) { return this.kayit('WARNING', m, b) }
  hata(m: string | Error, b?: Record<string, unknown>): Promise<boolean> {
    const mesaj = m instanceof Error ? m.message : m
    const ek = m instanceof Error ? { ...b, stack: (m.stack ?? '').slice(0, 3000) } : b
    return this.kayit('ERROR', mesaj, ek)
  }
  cokme(m: string | Error, b?: Record<string, unknown>): Promise<boolean> {
    const mesaj = m instanceof Error ? m.message : m
    const ek = m instanceof Error ? { ...b, stack: (m.stack ?? '').slice(0, 3000) } : b
    return this.kayit('CRITICAL', mesaj, ek)
  }

  /** Yakalanmamış hataları ve sözleri otomatik toplar. Tarayıcıda bir kez çağrılır. */
  globalYakalayicilariKur(): void {
    if (typeof window === 'undefined') return
    const w = window as unknown as { __bulutLoggerKurulu?: boolean }
    if (w.__bulutLoggerKurulu) return
    w.__bulutLoggerKurulu = true

    window.addEventListener('error', (olay) => {
      this.cokme(olay.error instanceof Error ? olay.error : olay.message, {
        kaynak: olay.filename,
        satir: olay.lineno,
        sutun: olay.colno
      })
    })

    window.addEventListener('unhandledrejection', (olay) => {
      const sebep = (olay as PromiseRejectionEvent).reason
      this.cokme(sebep instanceof Error ? sebep : String(sebep), { tur: 'unhandledrejection' })
    })
  }
}

export function loggerOlustur(ayarlar: LoggerAyarlari): BulutLogger {
  return new BulutLogger(ayarlar)
}

# MicroIPTool

🇬🇧 English version: [README.md](README.md)

A MicroIPTool egy egyszerű grafikus hálózati segédprogram Windows rendszerre, amely a mindennapi hálózati beállításokat és diagnosztikát hivatott megkönnyíteni.

## ⚙️ Funkciók

* Hálózati adapterek listázása
* Adapterek adatainak megjelenítése
* IP beállítások konfigurálása:

  * DHCP mód
  * Statikus IP cím
* Megadott IP cím pingelése
* Alap hálózati szkennelés (ping sweep)
* Állítható alkalmazás-betűméret
* Többnyelvű felület:

  * Magyar
  * Angol
* Hibák naplózása fájlba

## 📌 Állapot

Verzió: **1.0.0**

Első stabil kiadás.

## 💻 Követelmények

* Windows 10/11 operációs rendszer
* Rendszergazdai jogosultság (IP beállítás módosításához szükséges)

## ▶️ Használat

Telepítés nem szükséges.

1. Indítsd el az `.exe` fájlt
2. Válaszd ki a kívánt hálózati adaptert
3. Állítsd be az IP-t vagy használd a ping / scan funkciókat

## 🌐 Nyelv

Az alkalmazás támogatja a magyar és angol nyelvet.
A nyelv a menüből váltható.

## 🛡️ Biztonsági megjegyzés

A futtatható fájl vírusellenőrzésen esett át.

A PyInstaller használata miatt előfordulhat, hogy egyes vírusirtók hamis pozitív riasztást adnak.

A program biztonságosan használható, ha a hivatalos GitHub tárolóból lett letöltve.

VirusTotal ellenőrzés:
https://www.virustotal.com/gui/file/0d0353bc30a0a94dce2248e29d6b5cb0cf0ea136137a5a8d0d4a75ef86616592/detection

## 📝 Megjegyzés

A program eredetileg saját használatra készült, majd később került megosztásra.

A fejlesztés folyamatos, a funkciók a jövőben változhatnak.

## 📄 Változások

### v1.0.0

* Állítható betűméret beállítás hozzáadása
* Szkennelési tartomány kezelésének javítása
* IP cím mezők billentyűzetkezelési hibájának javítása (a Shift billentyű már nem léptet a következő mezőre)
* Általános stabilitási és használhatósági fejlesztések

### v0.8.1

* Szkennelés stabilitásának javítása
* Pontosabb eszközfelismerés szkennelés során
* Betűméret növelése a jobb olvashatóság érdekében

### v0.8

* Első publikus verzió
* IP beállítás
* Ping funkció
* Alap hálózati szkennelés

## 👤 Készítő

Mózes Balázs (Nozy82)

## 🔗 GitHub

https://github.com/Nozy82/MicroIPTool

## 📄 Licenc

MIT License

# Iskolacsengő
A Raspberry Pi controlled school bell system. - Egy iskolai csengővezérlő Raspberry Pivel meghajtva.

## Funkciók
- vezérlés böngészőből (a Pi újraindítása és leállítása is lehetséges böngészőből)
- több felhasználó támogatása
- több csengetési rend mentése
- csengetési rendek hozzárendelése napokhoz
- fájlok feltöltése böngészőből
- felhasználók létrehozása és törlése böngészőből
- beállítások módosítása böngészőből
- egyedi csengetési hangok beállítása adott napra (így megoldható, hogy adott napon, adott tanórán más legyen pl. a kicsengetés)
- csengetési renden kívüli bejátszások (pl. rádióműsor)
- csengetés szüneteltetése
- fájlok manuális lejátszása
- hiba esetén automatikus újraindulás
- hangerő módosítása böngészőből

## Telepítés
A program Raspberry Pi-re van tervezve, de megfelelő körülmények között más rendszeren is futtatható!

1. Klónozzuk ezt a repository-t!
2. Nyissuk meg a mappát a terminálban és adjuk ki a `sudo ./install.sh` parancsot! Ehhez előfordulhat, hogy meg kell adni a Raspberry Pi OS telepítésekor megadott jelszavunkat.
3. Ezután ha minden sikerült már fut is a program, melyet az 5000-es porton érhetünk el (ezt elérhetjük más eszközről is, ehhez írjuk be a böngészőbe a Raspberry Pi IP címét, vagy a korábban beállított hostname-et és a végére írjuk oda: *:5000*. Meg is nézhetjük a program státuszát ha terminálba begépeljük a következőt: `sudo systemctl status iskolacsengo.service`.
4. A program leállításhoz adjuk ki a `sudo systemctl stop iskolacsengo.service` parancsot!

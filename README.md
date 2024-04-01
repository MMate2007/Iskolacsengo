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
- egyedi csengetési hangok beállítása adott napra
- csengetés szüneteltetése
- fájlok manuális lejátszása

## Telepítés
Előfeltételek:
  - Python legalább 3-as verziója

1. Klónozzuk ezt a repository-t!
2. Készítsünk másolatot az *example.programmes.json* fájlból, s mentsük el tetszőleges néven! Ebből a fájlból annyi másolatot készítsünk, ahány csengetési rendet szeretnénk tárolni.
3. Szerkesszük ezt a fájlt a minta szerint! Fontos, hogy minden sor **kivéve az utolsó sor** (az adott zárójelen belül) végére kell vesszőt tenni!
4. A *settings.json* fájlt megnyitva adjuk meg az imént létrehozott fájl elérési útját (ha többet hoztunk létre, akkor azét adjuk meg, amelyet szeretnénk, hogy a program kövessen)! Ha egy nap másik csengetési rendet szeretnénk alkalmazni, akkor a program futtatása előtt módosítsuk a *settings.json* fájlt!
5. Adjuk ki a mappában a `pip install -r requirements.txt` parancsot! Ez telepíti a szükséges könyvtárakat.
6. Ha készen állunk, akkor elindíthatjuk a programot a `python main.py` parancs kiadásával.
7. Ha le szeretnénk állítani, akkor nyomjuk le a *Ctrl + C* billentyűket.

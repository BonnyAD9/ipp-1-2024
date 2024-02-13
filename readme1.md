# Implementační dokumentace k 1. úloze do IPP 2023/2024

**Jakub Antonín Štigler**\
Login: **xstigl00**

## Obecné informace

Implementaci jsem rozdělil do 4 souborů:
- `parse.py` obsahuje *main*, a část generace XML.
- `lexer.py` obsahuje třídy `Lexer`, `Token` a `TokenType`
- `ipp24_parser.py` obsahuje třídy `Parser`, `Instruction` a `Arg`
- `args.py` obsahuje kód pro parsování argumentů příkazové řádky
- `errors.py` obsahuje enumeraci s pojmenováním návratových kódů
- `statp.py` obsahuje kód pro sbírání statistik

Úplně na konci souboru `parse.py` se spouští funkce `main` která se nachází na
začátku souboru. Toto je první funkce co se spouští. Při spouštění funkce
`main` se i ověřují vyjímky aby se správně vrátil návratový kód *99* v
případech nečekaných chyb.

Při psaní kódu jsem se vyhýbal využívání vyjímek pro propagaci chyb v případech
kdy se předpoká že chyby nastanou za normálního běhu programu, protože vyjímky
jsou drahé.

## Rozdělení do tříd

Implementaci jsem se rozhodl rozdělit do několika tříd. Třídy `Lexer` a
`Parser` slouží pro rozdělení problému na dva menší podproblémy. Třída `Token`
slouží pro komunikaci mezi třídami `Lexer` a `Parser`. Třídy `Insttruction` a
`Arg` slouží hlavně pro uložení interní reprezentace zpracovaného kódu jazyka
IPPcode24. Dále se zde vyskytují různé další pomocné třídy a enumerace, které
už však nejsou tak důležité/zajímavé.

### Třída `Lexer` a `Token`

Nachází se v souboru `lexer.py`.

Třída `Lexer` slouží pro rozdělení kódu v textové reprezentaci ze vstupu do
tokenů, které o sobě ukládají typ a popřípadě data o daném tokenu. Všechny data
se ukládají v textové podobě, protože se budou serializovat zpět do xml a není
potřeba znát nebo pracovat s konkrétní hodnotou dat.

Mezy typy tokenů patří i `NEWLINE` který značí nový řádek, protože hranice
instrukcí se rozlišují podle nového řádku. Také zde je typ `ERR` který značí
že token je chybný.

Jediná veřejná metoda třídy `Lexer` je metoda `next` která vrátí další token
přečtený ze vstupu. Lexikální analýzu jsem se rozhodl implementovat trochu
nestandartním a míň obecným způsobem, protože jazyk IFJcode24 je ohldně
lexikální analýzy velmi jednoduchý na zpracování a protože python je pomalý
jazyk a zpracování znak po znaku by bylo neefektivní.

Vstup se čte po řádcích a každý řádek se rozdělí podle bílých znaků na menší
části kde z každé části vznikne jeden token. Tyto tokeny se poté uloží do
`Lexer.queue`. Metoda `next` se tedy podívá jestli ještě jsou nějaké zpracované
tokeny v `queue` a pokud ne, tak zpracuje další řádek ze vstupu. V `queue` jsou
zpracované tokeny v takovém pořadí že první token na řadě je na konci, aby se
dal efektivně oddělat.

Při zpracovávání tokenů se ověřuje že jsou tokeny validní. Při složitějších
typech tokenů (např. číselný literál) se na toto ověřování využívá *RegEx*.

### Třída `Parser`, `Instruction` a `Arg`

Nachází se v souboru `ipp24_parser.py`.

Třída `Parser` postupně zpracovává tokeny získané pomocí lexeru a z nich tvoří
list obsahující instance tříd `Instruction`. Třída `Instruction` obsahuje
`opcode` a list argumentů v podobě listu instancí tříd `Arg`. Třída `Arg`
je velmi podobná třídě `Token`. Rozdíl je že třída arg může mít jen některé z
typů, které má třída `Token`.

Jedinou veřejnou metodou třídy `Parser` je metoda `parse`, která zpracuje
všechny tokeny do listu instrukcí. Pokud nastane chyba tak, se vrací prázdný
list instrukcí a informace o chybě se nachází v `Parser.err_code` a
`Parser.err_msg`.

Při parsování kódu se nejdříve ověří že se na začátku nachází hlavička
`.IPPcode24` a dále se načítají instrukce. Instrukce se vždy načítají ve tvaru
*\<opcode\> [\<arg1\> [\<arg2\> \[...]]]* kde *\<opcode\>* je vždy token typu
`LABEL` a *\<argN\>* je token jednoho z typů: `LABEL`, `IDENT`, `NIL`, `BOOL`,
`INT`, `STRING`, `TYPE`.

Instrukce se po načtení vždy ověří pomocí metody `Instruction.validate`.
Ověření probíhá podle globální konstantní tabulky `_INSTRUCTIONS`, která pro
každou instrukci obsahuje list listů typů pro argumenty na stejné pozici.
Speciální případ je typ tokenu `TYPE`. Tento typ nikdy není vrácen lexerem
protože při lexikální analýze jej není možné rozlišit od tokenu typu `LABEL`.
Proto se při ověřování může za určitých podmínek převést argument typu `LABEL`
na argument typu `TYPE`.

## Převod do XML

Pro převod do XML nepoužívám žádnou knihovnu, protože převod je v tomto případě
jednoduchý a použití knihovny by jej zjednodušilo jen trochu. Převod probíhá
pomocí funkce `make_xml` v souboru `parse.py` a pomocí metod
`Instruction.write_xml` a `Arg.write_xml`.

Funkce `make_xml` se stará o generování XML hlavičky, tagu `<program>` a volá
metodu `Instruction.write_xml` pro všechny instrukce. Ta se stará o generování
tagu `<instruction>` a volá metodu `Arg.write_xml` pro všechny parametry. Ta
se potom stará o generování tagů `<arg1>`, `<arg2>` a `<arg3>`. Teoreticky
by mohla vygenerovat i tagy `<arg4>` a dále, ale to nikdy nenastane, protože
to nedovoluje žádná instrukce v tabulce `_INSTRUCTIONS`.

## STATP

Implementace pro rozšíření *STATP* se nachází v souboru `statp.py`.

Všechny statistiky kromě počtu komentářů se získávají až po zparsování kódu.
Statistiky o komentářích se získávají při tokenizaci už v lexeru protože dále
jsou už komentáře igorované.

Statistiky které vyžadují průchod přes instrukce se nepočítají pokud nejsou
potřeba. Když jsou ale potřeba tak se už spočítají všechny statistiky v jednom
průuchodu. Pokud už jsou statistiky jednou spočítané tak se už nepočítají znovu
ale už se jen využívá ta jednou spočítaná hodnota.

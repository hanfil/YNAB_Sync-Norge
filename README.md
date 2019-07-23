# YNAB Sync
Applikasjon for å synke transaksjoner fra SBanken til YNAB.

[Last ned her](https://github.com/hanfil/YNAB_Sync-Norge/releases)

![App](https://raw.githubusercontent.com/hanfil/YNAB_Sync-Norge/master/doc/app_info.png)

Betalingsmottaker (payee) og kategori må settes manuelt i etterkant, og transaksjonen må verifieseres i YNAB-appen eller på app.ynab.com. 

## Autentisering
Både YNAB og SBanken benytter seg av autentiseringstoken for å godta påloggingsforsøk.  Disse må hentes fra de respektive utviklersidene. 

### SBanken
For å kunne benytte seg SBanken sin API, må man inngå en utvikleravtale med SBanken.  Se https://secure.sbanken.no/Personal/ApiBeta/Info/. 

![Sbanken avtale](https://gitlab.com/ljantzen/moneyplan/raw/master/docs/images/sbanken-avtale.png)

Etter at avtalen er inngått, har man muligheten til å opprette autentiseringstoken.  Det gjør du i Utviklerportalen.

![Utviklerportalen](https://gitlab.com/ljantzen/moneyplan/raw/master/docs/images/utviklerportalen.png)

Her skal du først opprette en applikasjon, og så generere en token.
Applikasjonen trenger visse lese rettigheter for å hente ut transaksjoner.
_IKKE huk av på "Grants full access to the eFakturas service." og "Grants full access to the transfers service." Så slipper du at andre kan misbruke banken din._

![Sbanken_apitoken](https://gitlab.com/ljantzen/moneyplan/raw/master/docs/images/sbanken-apitoken.png)


Applikasjonsnøkkel i Sbanken skal inn i "SBank clientid" under settings.  Applikasjonspassordet henter du ved å trykke på 
_Bestill nytt passord._  Det må du skrive net et sted, for det blir ikke vist på nytt.
Applikasjonspassordet i Sbanken skal inn i "SBank secret"

![Sbanken_input](https://raw.githubusercontent.com/hanfil/YNAB_Sync-Norge/master/doc/app_settings.png)

### Pålogging YNAB 

YNAB har også en autentiseringstoken.  Etter innlogging går du til https://app.youneedabudget.com/settings/developer og trykker på knappen 'NewToken'

![New Token](https://gitlab.com/ljantzen/moneyplan/raw/master/docs/images/ynabtoken.png)

## Load (Start)

Når du har fylt ut de øverste feltene så kan du klikke _Hent YNAB Budgets_. Nå vil du ha mulighet til å velge et budget fra YNAB.

Etter at du har valgt YNAB Budgettet så kan du begynne å linke en konto fra SBanken til en konto i YNAB. Klikk _Hent YNAB og SBAnken kontoer_ for hente inn kontoene.
Velg en i hver list og klikk _Link kontoene_.

Merk deg feltet "_start-date_". Der kan du velge når programmet skal starte å synce transaksjoner fra. Anbefaler at du ikke tar den så langt bak i tid. Start med de siste 30 dagene.

Når du har linket alle kontoene du ønsker så kan du klikke _Load (Start)_. 
Nå vil programmet begynne å se om den finner matchende transaksjoner mellom YNAB og SBanken, og opprette de den ikke finner i YNAB.
Programmet har som standard 4 dagers fortidsjekk, for å se om transaksjoen er blitt opprettet tidligere i YNAB. Men den standarden kan endres under _Settings_.


[comment]: <> (Transform to PDF -> https://dillinger.io/)
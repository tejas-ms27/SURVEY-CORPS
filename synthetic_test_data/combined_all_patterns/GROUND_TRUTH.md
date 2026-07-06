# Combined All Patterns — Full Regression Set

## Objective

Detects when the exact same transaction row appears twice in a statement. Both rows share the same reference number, amount, and narration — evidence of a processing error or deliberate manipulation.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Mixed Subject | `0642911656685344-01-12-2024to08-05-2026.csv` | BANK OF BARODA | 0642911656685344 |
| Mixed Subject | `9592043503463703-02-12-2024to09-05-2026.csv` | BANK OF BARODA | 9592043503463703 |
| Mixed Subject | `92626656155172 statement.csv` | HDFC BANK LTD | 92626656155172 |
| Mixed Subject | `06555427844681-01-12-2024to08-05-2026.csv` | THE FEDERAL BANK LIMITED | 06555427844681 |
| Mixed Subject | `6369331266799686-01-12-2024to09-05-2026.pdf` | BANK OF INDIA | 6369331266799686 |
| Mixed Subject | `55794792847269-01-12-2024to09-05-2026.pdf` | THE FEDERAL BANK LIMITED | 55794792847269 |
| Mixed Subject | `9454583674913372-02-12-2024to09-05-2026.pdf` | UCO BANK | 9454583674913372 |
| Mixed Subject | `3185728472711726-01-12-2024to09-05-2026.xlsx` | BANK OF BARODA | 3185728472711726 |
| Mixed Subject | `00837844971737-01-12-2024to09-05-2026.csv` | THE FEDERAL BANK LIMITED | 00837844971737 |
| Mixed Subject | `3922181054742642-01-12-2024to08-05-2026.xlsx` | BANK OF INDIA | 3922181054742642 |
| Mixed Subject | `9791722953307803-01-12-2024to09-05-2026.csv` | BANK OF BARODA | 9791722953307803 |
| Mixed Subject | `1157402870460715_statement.pdf` | PUNJAB NATIONAL BANK | 1157402870460715 |
| Mixed Subject | `2074341316704650-01-12-2024to09-05-2026.xlsx` | UCO BANK | 2074341316704650 |
| Mixed Subject | `statement-64831176837.csv` | STATE BANK OF INDIA | 64831176837 |
| Mixed Subject | `49914742547252_SOA.pdf` | BANDHAN BANK LIMITED | 49914742547252 |
| Mixed Subject | `26278416411428_SOA.pdf` | BANDHAN BANK LIMITED | 26278416411428 |
| Mixed Subject | `6912827621_statement.pdf` | KOTAK MAHINDRA BANK LTD | 6912827621 |
| Mixed Subject | `99132894316457 statement.csv` | HDFC BANK LTD | 99132894316457 |
| Mixed Subject | `6082267802022370-01-12-2024to08-05-2026.csv` | BANK OF INDIA | 6082267802022370 |
| Mixed Subject | `93649988897865-25-12-2024to04-11-2025.pdf` | THE FEDERAL BANK LIMITED | 93649988897865 |
| Mixed Subject | `940797593562472_statement.csv` | AXIS BANK LIMITED | 940797593562472 |
| Mixed Subject | `9824732161017095_statement.txt` | PUNJAB NATIONAL BANK | 9824732161017095 |
| Clean Control | `63265662163410 statement.pdf` | HDFC BANK LTD | 63265662163410 |
| Clean Control | `5790161720_statement.csv` | KOTAK MAHINDRA BANK LTD | 5790161720 |
| Clean Control | `statement-45621471291.txt` | STATE BANK OF INDIA | 45621471291 |
| Clean Control | `823769802355587_statement.csv` | AXIS BANK LIMITED | 823769802355587 |
| Clean Control | `3557968594061190-01-12-2024to08-05-2026.pdf` | BANK OF BARODA | 3557968594061190 |
| Clean Control | `33565604015218 statement.csv` | HDFC BANK LTD | 33565604015218 |
| Clean Control | `76525930328394-01-12-2024to09-05-2026.xlsx` | THE FEDERAL BANK LIMITED | 76525930328394 |
| Clean Control | `46222788658678-02-12-2024to09-05-2026.csv` | THE FEDERAL BANK LIMITED | 46222788658678 |
| Clean Control | `648876988058022_statement.csv` | AXIS BANK LIMITED | 648876988058022 |
| Clean Control | `5110050321418371-02-12-2024to09-05-2026.pdf` | UCO BANK | 5110050321418371 |
| Clean Control | `6590397142208598-01-12-2024to09-05-2026.csv` | BANK OF BARODA | 6590397142208598 |
| Clean Control | `22200566550577 statement.pdf` | HDFC BANK LTD | 22200566550577 |
| Clean Control | `25504642312445 statement.csv` | HDFC BANK LTD | 25504642312445 |
| Clean Control | `66018180252877-02-12-2024to09-05-2026.xlsx` | THE FEDERAL BANK LIMITED | 66018180252877 |
| Clean Control | `17827883120358 statement.csv` | HDFC BANK LTD | 17827883120358 |
| Clean Control | `6647179986284826-01-12-2024to09-05-2026.pdf` | UCO BANK | 6647179986284826 |
| Clean Control | `3805938186_statement.pdf` | KOTAK MAHINDRA BANK LTD | 3805938186 |
| Clean Control | `7914559016093548-01-12-2024to09-05-2026.pdf` | UCO BANK | 7914559016093548 |
| Clean Control | `6141243112779930-01-12-2024to09-05-2026.xlsx` | BANK OF BARODA | 6141243112779930 |
| Clean Control | `95486075400783_SOA.pdf` | BANDHAN BANK LIMITED | 95486075400783 |
| Clean Control | `6773870626175302-01-12-2024to09-05-2026.pdf` | BANK OF INDIA | 6773870626175302 |
| Clean Control | `8424611488710543-01-12-2024to09-05-2026.xlsx` | BANK OF INDIA | 8424611488710543 |
| Clean Control | `12244398223872_SOA.xlsx` | BANDHAN BANK LIMITED | 12244398223872 |
| Clean Control | `06413212528833-01-12-2024to08-05-2026.pdf` | THE FEDERAL BANK LIMITED | 06413212528833 |
| Clean Control | `statement-50632066232.csv` | STATE BANK OF INDIA | 50632066232 |
| Clean Control | `0829992362_statement.pdf` | KOTAK MAHINDRA BANK LTD | 0829992362 |
| Clean Control | `21733893993601-01-12-2024to09-05-2026.pdf` | THE FEDERAL BANK LIMITED | 21733893993601 |
| Clean Control | `980588499302989_statement.csv` | AXIS BANK LIMITED | 980588499302989 |
| Clean Control | `58685988238063 statement.csv` | HDFC BANK LTD | 58685988238063 |
| Clean Control | `0000523958365677-01-12-2024to09-05-2026.xlsx` | BANK OF INDIA | 0000523958365677 |
| Clean Control | `20277882554687 statement.xlsx` | HDFC BANK LTD | 20277882554687 |
| Clean Control | `2574702189_statement.pdf` | KOTAK MAHINDRA BANK LTD | 2574702189 |
| Clean Control | `statement-99257469544.xlsx` | STATE BANK OF INDIA | 99257469544 |
| Clean Control | `4170120848414864_statement.xlsx` | PUNJAB NATIONAL BANK | 4170120848414864 |
| Clean Control | `19721381060384-01-12-2024to09-05-2026.csv` | THE FEDERAL BANK LIMITED | 19721381060384 |
| Clean Control | `83253542733693 statement.csv` | HDFC BANK LTD | 83253542733693 |
| Clean Control | `1141802045660774_statement.txt` | PUNJAB NATIONAL BANK | 1141802045660774 |
| Clean Control | `1953122382303283_statement.txt` | PUNJAB NATIONAL BANK | 1953122382303283 |
| Clean Control | `3002489826_statement.csv` | KOTAK MAHINDRA BANK LTD | 3002489826 |
| Clean Control | `84709757456713-01-12-2024to09-05-2026.csv` | THE FEDERAL BANK LIMITED | 84709757456713 |
| Clean Control | `0215264398_statement.pdf` | KOTAK MAHINDRA BANK LTD | 0215264398 |
| Clean Control | `9892156611_statement.csv` | KOTAK MAHINDRA BANK LTD | 9892156611 |
| Clean Control | `13795462330102_SOA.xlsx` | BANDHAN BANK LIMITED | 13795462330102 |
| Clean Control | `39093477733984_SOA.pdf` | BANDHAN BANK LIMITED | 39093477733984 |
| Clean Control | `statement-16014463919.csv` | STATE BANK OF INDIA | 16014463919 |
| Clean Control | `7128594441726646-01-12-2024to09-05-2026.xlsx` | BANK OF BARODA | 7128594441726646 |
| Clean Control | `49987608838385_SOA.csv` | BANDHAN BANK LIMITED | 49987608838385 |
| Clean Control | `6763736309111698-01-12-2024to09-05-2026.xlsx` | BANK OF INDIA | 6763736309111698 |
| Clean Control | `4462814073923973-01-12-2024to09-05-2026.csv` | BANK OF INDIA | 4462814073923973 |
| Clean Control | `7210891757897345-01-12-2024to09-05-2026.xlsx` | UCO BANK | 7210891757897345 |
| Clean Control | `statement-91533868610.csv` | STATE BANK OF INDIA | 91533868610 |
| Clean Control | `307456363299274_statement.csv` | AXIS BANK LIMITED | 307456363299274 |
| Clean Control | `6096313711_statement.pdf` | KOTAK MAHINDRA BANK LTD | 6096313711 |
| Clean Control | `08962225500023 statement.pdf` | HDFC BANK LTD | 08962225500023 |
| Clean Control | `32456679929231-02-12-2024to09-05-2026.pdf` | THE FEDERAL BANK LIMITED | 32456679929231 |
| Clean Control | `47455115930805 statement.pdf` | HDFC BANK LTD | 47455115930805 |
| Clean Control | `94460602942528_SOA.csv` | BANDHAN BANK LIMITED | 94460602942528 |
| Clean Control | `8046594937484611-01-12-2024to09-05-2026.xlsx` | UCO BANK | 8046594937484611 |
| Clean Control | `1758205321341929_statement.pdf` | PUNJAB NATIONAL BANK | 1758205321341929 |
| Clean Control | `statement-23372099801.txt` | STATE BANK OF INDIA | 23372099801 |
| Clean Control | `statement-25429361452.xlsx` | STATE BANK OF INDIA | 25429361452 |
| Clean Control | `351544452945333_statement.csv` | AXIS BANK LIMITED | 351544452945333 |
| Clean Control | `1064048852061172-01-12-2024to09-05-2026.pdf` | UCO BANK | 1064048852061172 |
| Clean Control | `statement-71297095228.txt` | STATE BANK OF INDIA | 71297095228 |
| Clean Control | `67031820584641_SOA.xlsx` | BANDHAN BANK LIMITED | 67031820584641 |
| Clean Control | `7523479214_statement.pdf` | KOTAK MAHINDRA BANK LTD | 7523479214 |
| Clean Control | `68327262930584_SOA.pdf` | BANDHAN BANK LIMITED | 68327262930584 |
| Clean Control | `01541244528922_SOA.csv` | BANDHAN BANK LIMITED | 01541244528922 |
| Clean Control | `19767703151236_SOA.csv` | BANDHAN BANK LIMITED | 19767703151236 |
| Clean Control | `280740546792734_statement.csv` | AXIS BANK LIMITED | 280740546792734 |
| Clean Control | `42224070805318 statement.pdf` | HDFC BANK LTD | 42224070805318 |
| Clean Control | `6716734979076008_statement.pdf` | PUNJAB NATIONAL BANK | 6716734979076008 |
| Clean Control | `063451453499090_statement.pdf` | AXIS BANK LIMITED | 063451453499090 |
| Clean Control | `9812985728772256-01-12-2024to09-05-2026.xlsx` | BANK OF BARODA | 9812985728772256 |

## Accounts Involved

### Mixed Subject — BANK OF BARODA · 0642911656685344
- **Statement:** `0642911656685344-01-12-2024to08-05-2026.csv`
- **Full File Path:** `statements/0642911656685344-01-12-2024to08-05-2026.csv`

### Mixed Subject — BANK OF BARODA · 9592043503463703
- **Statement:** `9592043503463703-02-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/9592043503463703-02-12-2024to09-05-2026.csv`

### Mixed Subject — HDFC BANK LTD · 92626656155172
- **Statement:** `92626656155172 statement.csv`
- **Full File Path:** `statements/92626656155172 statement.csv`

### Mixed Subject — THE FEDERAL BANK LIMITED · 06555427844681
- **Statement:** `06555427844681-01-12-2024to08-05-2026.csv`
- **Full File Path:** `statements/06555427844681-01-12-2024to08-05-2026.csv`

### Mixed Subject — BANK OF INDIA · 6369331266799686
- **Statement:** `6369331266799686-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/6369331266799686-01-12-2024to09-05-2026.pdf`

### Mixed Subject — THE FEDERAL BANK LIMITED · 55794792847269
- **Statement:** `55794792847269-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/55794792847269-01-12-2024to09-05-2026.pdf`

### Mixed Subject — UCO BANK · 9454583674913372
- **Statement:** `9454583674913372-02-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/9454583674913372-02-12-2024to09-05-2026.pdf`

### Mixed Subject — BANK OF BARODA · 3185728472711726
- **Statement:** `3185728472711726-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/3185728472711726-01-12-2024to09-05-2026.xlsx`

### Mixed Subject — THE FEDERAL BANK LIMITED · 00837844971737
- **Statement:** `00837844971737-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/00837844971737-01-12-2024to09-05-2026.csv`

### Mixed Subject — BANK OF INDIA · 3922181054742642
- **Statement:** `3922181054742642-01-12-2024to08-05-2026.xlsx`
- **Full File Path:** `statements/3922181054742642-01-12-2024to08-05-2026.xlsx`

### Mixed Subject — BANK OF BARODA · 9791722953307803
- **Statement:** `9791722953307803-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/9791722953307803-01-12-2024to09-05-2026.csv`

### Mixed Subject — PUNJAB NATIONAL BANK · 1157402870460715
- **Statement:** `1157402870460715_statement.pdf`
- **Full File Path:** `statements/1157402870460715_statement.pdf`

### Mixed Subject — UCO BANK · 2074341316704650
- **Statement:** `2074341316704650-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/2074341316704650-01-12-2024to09-05-2026.xlsx`

### Mixed Subject — STATE BANK OF INDIA · 64831176837
- **Statement:** `statement-64831176837.csv`
- **Full File Path:** `statements/statement-64831176837.csv`

### Mixed Subject — BANDHAN BANK LIMITED · 49914742547252
- **Statement:** `49914742547252_SOA.pdf`
- **Full File Path:** `statements/49914742547252_SOA.pdf`

### Mixed Subject — BANDHAN BANK LIMITED · 26278416411428
- **Statement:** `26278416411428_SOA.pdf`
- **Full File Path:** `statements/26278416411428_SOA.pdf`

### Mixed Subject — KOTAK MAHINDRA BANK LTD · 6912827621
- **Statement:** `6912827621_statement.pdf`
- **Full File Path:** `statements/6912827621_statement.pdf`

### Mixed Subject — HDFC BANK LTD · 99132894316457
- **Statement:** `99132894316457 statement.csv`
- **Full File Path:** `statements/99132894316457 statement.csv`

### Mixed Subject — BANK OF INDIA · 6082267802022370
- **Statement:** `6082267802022370-01-12-2024to08-05-2026.csv`
- **Full File Path:** `statements/6082267802022370-01-12-2024to08-05-2026.csv`

### Mixed Subject — THE FEDERAL BANK LIMITED · 93649988897865
- **Statement:** `93649988897865-25-12-2024to04-11-2025.pdf`
- **Full File Path:** `statements/93649988897865-25-12-2024to04-11-2025.pdf`

### Mixed Subject — AXIS BANK LIMITED · 940797593562472
- **Statement:** `940797593562472_statement.csv`
- **Full File Path:** `statements/940797593562472_statement.csv`

### Mixed Subject — PUNJAB NATIONAL BANK · 9824732161017095
- **Statement:** `9824732161017095_statement.txt`
- **Full File Path:** `statements/9824732161017095_statement.txt`

### Clean Control — HDFC BANK LTD · 63265662163410
- **Statement:** `63265662163410 statement.pdf`
- **Full File Path:** `statements/63265662163410 statement.pdf`

### Clean Control — KOTAK MAHINDRA BANK LTD · 5790161720
- **Statement:** `5790161720_statement.csv`
- **Full File Path:** `statements/5790161720_statement.csv`

### Clean Control — STATE BANK OF INDIA · 45621471291
- **Statement:** `statement-45621471291.txt`
- **Full File Path:** `statements/statement-45621471291.txt`

### Clean Control — AXIS BANK LIMITED · 823769802355587
- **Statement:** `823769802355587_statement.csv`
- **Full File Path:** `statements/823769802355587_statement.csv`

### Clean Control — BANK OF BARODA · 3557968594061190
- **Statement:** `3557968594061190-01-12-2024to08-05-2026.pdf`
- **Full File Path:** `statements/3557968594061190-01-12-2024to08-05-2026.pdf`

### Clean Control — HDFC BANK LTD · 33565604015218
- **Statement:** `33565604015218 statement.csv`
- **Full File Path:** `statements/33565604015218 statement.csv`

### Clean Control — THE FEDERAL BANK LIMITED · 76525930328394
- **Statement:** `76525930328394-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/76525930328394-01-12-2024to09-05-2026.xlsx`

### Clean Control — THE FEDERAL BANK LIMITED · 46222788658678
- **Statement:** `46222788658678-02-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/46222788658678-02-12-2024to09-05-2026.csv`

### Clean Control — AXIS BANK LIMITED · 648876988058022
- **Statement:** `648876988058022_statement.csv`
- **Full File Path:** `statements/648876988058022_statement.csv`

### Clean Control — UCO BANK · 5110050321418371
- **Statement:** `5110050321418371-02-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/5110050321418371-02-12-2024to09-05-2026.pdf`

### Clean Control — BANK OF BARODA · 6590397142208598
- **Statement:** `6590397142208598-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/6590397142208598-01-12-2024to09-05-2026.csv`

### Clean Control — HDFC BANK LTD · 22200566550577
- **Statement:** `22200566550577 statement.pdf`
- **Full File Path:** `statements/22200566550577 statement.pdf`

### Clean Control — HDFC BANK LTD · 25504642312445
- **Statement:** `25504642312445 statement.csv`
- **Full File Path:** `statements/25504642312445 statement.csv`

### Clean Control — THE FEDERAL BANK LIMITED · 66018180252877
- **Statement:** `66018180252877-02-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/66018180252877-02-12-2024to09-05-2026.xlsx`

### Clean Control — HDFC BANK LTD · 17827883120358
- **Statement:** `17827883120358 statement.csv`
- **Full File Path:** `statements/17827883120358 statement.csv`

### Clean Control — UCO BANK · 6647179986284826
- **Statement:** `6647179986284826-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/6647179986284826-01-12-2024to09-05-2026.pdf`

### Clean Control — KOTAK MAHINDRA BANK LTD · 3805938186
- **Statement:** `3805938186_statement.pdf`
- **Full File Path:** `statements/3805938186_statement.pdf`

### Clean Control — UCO BANK · 7914559016093548
- **Statement:** `7914559016093548-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/7914559016093548-01-12-2024to09-05-2026.pdf`

### Clean Control — BANK OF BARODA · 6141243112779930
- **Statement:** `6141243112779930-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/6141243112779930-01-12-2024to09-05-2026.xlsx`

### Clean Control — BANDHAN BANK LIMITED · 95486075400783
- **Statement:** `95486075400783_SOA.pdf`
- **Full File Path:** `statements/95486075400783_SOA.pdf`

### Clean Control — BANK OF INDIA · 6773870626175302
- **Statement:** `6773870626175302-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/6773870626175302-01-12-2024to09-05-2026.pdf`

### Clean Control — BANK OF INDIA · 8424611488710543
- **Statement:** `8424611488710543-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/8424611488710543-01-12-2024to09-05-2026.xlsx`

### Clean Control — BANDHAN BANK LIMITED · 12244398223872
- **Statement:** `12244398223872_SOA.xlsx`
- **Full File Path:** `statements/12244398223872_SOA.xlsx`

### Clean Control — THE FEDERAL BANK LIMITED · 06413212528833
- **Statement:** `06413212528833-01-12-2024to08-05-2026.pdf`
- **Full File Path:** `statements/06413212528833-01-12-2024to08-05-2026.pdf`

### Clean Control — STATE BANK OF INDIA · 50632066232
- **Statement:** `statement-50632066232.csv`
- **Full File Path:** `statements/statement-50632066232.csv`

### Clean Control — KOTAK MAHINDRA BANK LTD · 0829992362
- **Statement:** `0829992362_statement.pdf`
- **Full File Path:** `statements/0829992362_statement.pdf`

### Clean Control — THE FEDERAL BANK LIMITED · 21733893993601
- **Statement:** `21733893993601-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/21733893993601-01-12-2024to09-05-2026.pdf`

### Clean Control — AXIS BANK LIMITED · 980588499302989
- **Statement:** `980588499302989_statement.csv`
- **Full File Path:** `statements/980588499302989_statement.csv`

### Clean Control — HDFC BANK LTD · 58685988238063
- **Statement:** `58685988238063 statement.csv`
- **Full File Path:** `statements/58685988238063 statement.csv`

### Clean Control — BANK OF INDIA · 0000523958365677
- **Statement:** `0000523958365677-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/0000523958365677-01-12-2024to09-05-2026.xlsx`

### Clean Control — HDFC BANK LTD · 20277882554687
- **Statement:** `20277882554687 statement.xlsx`
- **Full File Path:** `statements/20277882554687 statement.xlsx`

### Clean Control — KOTAK MAHINDRA BANK LTD · 2574702189
- **Statement:** `2574702189_statement.pdf`
- **Full File Path:** `statements/2574702189_statement.pdf`

### Clean Control — STATE BANK OF INDIA · 99257469544
- **Statement:** `statement-99257469544.xlsx`
- **Full File Path:** `statements/statement-99257469544.xlsx`

### Clean Control — PUNJAB NATIONAL BANK · 4170120848414864
- **Statement:** `4170120848414864_statement.xlsx`
- **Full File Path:** `statements/4170120848414864_statement.xlsx`

### Clean Control — THE FEDERAL BANK LIMITED · 19721381060384
- **Statement:** `19721381060384-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/19721381060384-01-12-2024to09-05-2026.csv`

### Clean Control — HDFC BANK LTD · 83253542733693
- **Statement:** `83253542733693 statement.csv`
- **Full File Path:** `statements/83253542733693 statement.csv`

### Clean Control — PUNJAB NATIONAL BANK · 1141802045660774
- **Statement:** `1141802045660774_statement.txt`
- **Full File Path:** `statements/1141802045660774_statement.txt`

### Clean Control — PUNJAB NATIONAL BANK · 1953122382303283
- **Statement:** `1953122382303283_statement.txt`
- **Full File Path:** `statements/1953122382303283_statement.txt`

### Clean Control — KOTAK MAHINDRA BANK LTD · 3002489826
- **Statement:** `3002489826_statement.csv`
- **Full File Path:** `statements/3002489826_statement.csv`

### Clean Control — THE FEDERAL BANK LIMITED · 84709757456713
- **Statement:** `84709757456713-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/84709757456713-01-12-2024to09-05-2026.csv`

### Clean Control — KOTAK MAHINDRA BANK LTD · 0215264398
- **Statement:** `0215264398_statement.pdf`
- **Full File Path:** `statements/0215264398_statement.pdf`

### Clean Control — KOTAK MAHINDRA BANK LTD · 9892156611
- **Statement:** `9892156611_statement.csv`
- **Full File Path:** `statements/9892156611_statement.csv`

### Clean Control — BANDHAN BANK LIMITED · 13795462330102
- **Statement:** `13795462330102_SOA.xlsx`
- **Full File Path:** `statements/13795462330102_SOA.xlsx`

### Clean Control — BANDHAN BANK LIMITED · 39093477733984
- **Statement:** `39093477733984_SOA.pdf`
- **Full File Path:** `statements/39093477733984_SOA.pdf`

### Clean Control — STATE BANK OF INDIA · 16014463919
- **Statement:** `statement-16014463919.csv`
- **Full File Path:** `statements/statement-16014463919.csv`

### Clean Control — BANK OF BARODA · 7128594441726646
- **Statement:** `7128594441726646-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/7128594441726646-01-12-2024to09-05-2026.xlsx`

### Clean Control — BANDHAN BANK LIMITED · 49987608838385
- **Statement:** `49987608838385_SOA.csv`
- **Full File Path:** `statements/49987608838385_SOA.csv`

### Clean Control — BANK OF INDIA · 6763736309111698
- **Statement:** `6763736309111698-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/6763736309111698-01-12-2024to09-05-2026.xlsx`

### Clean Control — BANK OF INDIA · 4462814073923973
- **Statement:** `4462814073923973-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/4462814073923973-01-12-2024to09-05-2026.csv`

### Clean Control — UCO BANK · 7210891757897345
- **Statement:** `7210891757897345-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/7210891757897345-01-12-2024to09-05-2026.xlsx`

### Clean Control — STATE BANK OF INDIA · 91533868610
- **Statement:** `statement-91533868610.csv`
- **Full File Path:** `statements/statement-91533868610.csv`

### Clean Control — AXIS BANK LIMITED · 307456363299274
- **Statement:** `307456363299274_statement.csv`
- **Full File Path:** `statements/307456363299274_statement.csv`

### Clean Control — KOTAK MAHINDRA BANK LTD · 6096313711
- **Statement:** `6096313711_statement.pdf`
- **Full File Path:** `statements/6096313711_statement.pdf`

### Clean Control — HDFC BANK LTD · 08962225500023
- **Statement:** `08962225500023 statement.pdf`
- **Full File Path:** `statements/08962225500023 statement.pdf`

### Clean Control — THE FEDERAL BANK LIMITED · 32456679929231
- **Statement:** `32456679929231-02-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/32456679929231-02-12-2024to09-05-2026.pdf`

### Clean Control — HDFC BANK LTD · 47455115930805
- **Statement:** `47455115930805 statement.pdf`
- **Full File Path:** `statements/47455115930805 statement.pdf`

### Clean Control — BANDHAN BANK LIMITED · 94460602942528
- **Statement:** `94460602942528_SOA.csv`
- **Full File Path:** `statements/94460602942528_SOA.csv`

### Clean Control — UCO BANK · 8046594937484611
- **Statement:** `8046594937484611-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/8046594937484611-01-12-2024to09-05-2026.xlsx`

### Clean Control — PUNJAB NATIONAL BANK · 1758205321341929
- **Statement:** `1758205321341929_statement.pdf`
- **Full File Path:** `statements/1758205321341929_statement.pdf`

### Clean Control — STATE BANK OF INDIA · 23372099801
- **Statement:** `statement-23372099801.txt`
- **Full File Path:** `statements/statement-23372099801.txt`

### Clean Control — STATE BANK OF INDIA · 25429361452
- **Statement:** `statement-25429361452.xlsx`
- **Full File Path:** `statements/statement-25429361452.xlsx`

### Clean Control — AXIS BANK LIMITED · 351544452945333
- **Statement:** `351544452945333_statement.csv`
- **Full File Path:** `statements/351544452945333_statement.csv`

### Clean Control — UCO BANK · 1064048852061172
- **Statement:** `1064048852061172-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/1064048852061172-01-12-2024to09-05-2026.pdf`

### Clean Control — STATE BANK OF INDIA · 71297095228
- **Statement:** `statement-71297095228.txt`
- **Full File Path:** `statements/statement-71297095228.txt`

### Clean Control — BANDHAN BANK LIMITED · 67031820584641
- **Statement:** `67031820584641_SOA.xlsx`
- **Full File Path:** `statements/67031820584641_SOA.xlsx`

### Clean Control — KOTAK MAHINDRA BANK LTD · 7523479214
- **Statement:** `7523479214_statement.pdf`
- **Full File Path:** `statements/7523479214_statement.pdf`

### Clean Control — BANDHAN BANK LIMITED · 68327262930584
- **Statement:** `68327262930584_SOA.pdf`
- **Full File Path:** `statements/68327262930584_SOA.pdf`

### Clean Control — BANDHAN BANK LIMITED · 01541244528922
- **Statement:** `01541244528922_SOA.csv`
- **Full File Path:** `statements/01541244528922_SOA.csv`

### Clean Control — BANDHAN BANK LIMITED · 19767703151236
- **Statement:** `19767703151236_SOA.csv`
- **Full File Path:** `statements/19767703151236_SOA.csv`

### Clean Control — AXIS BANK LIMITED · 280740546792734
- **Statement:** `280740546792734_statement.csv`
- **Full File Path:** `statements/280740546792734_statement.csv`

### Clean Control — HDFC BANK LTD · 42224070805318
- **Statement:** `42224070805318 statement.pdf`
- **Full File Path:** `statements/42224070805318 statement.pdf`

### Clean Control — PUNJAB NATIONAL BANK · 6716734979076008
- **Statement:** `6716734979076008_statement.pdf`
- **Full File Path:** `statements/6716734979076008_statement.pdf`

### Clean Control — AXIS BANK LIMITED · 063451453499090
- **Statement:** `063451453499090_statement.pdf`
- **Full File Path:** `statements/063451453499090_statement.pdf`

### Clean Control — BANK OF BARODA · 9812985728772256
- **Statement:** `9812985728772256-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/9812985728772256-01-12-2024to09-05-2026.xlsx`

## Expected Findings

### Pattern 1 — Duplicate Verification

**Severity:** HIGH  
**Pattern ID:** 1  
**Amount:** ₹11,100.53  
**Reason:** Exact duplicate row embedded in realistic surrounding activity.  

**Accounts Involved:**

- **Mixed Subject** — BANK OF BARODA, Account `0642911656685344` (`0642911656685344-01-12-2024to08-05-2026.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 09-09-2025 | Credit/Debit | IMPS-I42508797913-Gaurav Joshi | IMPS-I42508797913-Gaurav Joshi | `I42508797913` |

### Pattern 2 — Failed Reversed Transaction

**Severity:** HIGH  
**Pattern ID:** 2  
**Amount:** ₹32,400.86  
**Reason:** Debit followed by credit reversal for the exact same amount.  

**Accounts Involved:**

- **Mixed Subject** — BANK OF BARODA, Account `9592043503463703` (`9592043503463703-02-12-2024to09-05-2026.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 20-09-2025 | Credit/Debit | NEFT/I11019007095/Vijay Jain | NEFT/I11019007095/Vijay Jain | `I11019007095` |
| 21-09-2025 | Credit | RETURN/I11019007095/TRANSACTION FAILED | RETURN/I11019007095/TRANSACTION FAILED | `077067624553` |

### Pattern 3 — Pass Through Routing

**Severity:** HIGH  
**Pattern ID:** 3  
**Amount Range:** ₹51,500.29 – ₹255,452.76  
**Reason:** Multiple unrelated inbound credits followed by rapid onward routing.  

**Accounts Involved:**

- **Mixed Subject** — HDFC BANK LTD, Account `92626656155172` (`92626656155172 statement.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 26/07/25 | Credit | UPI-Sangita Ahuja-sangita.ahuja@kotak-855989218645-CR VIA UPI | UPI-Sangita Ahuja-sangita.ahuja@kotak-855989218645-CR VIA UPI | `108083991909` |
| 26/07/25 | Credit | UPI-Abhishek Chopra-abhishekchop76@ibl-515310819699-CR VIA UPI | UPI-Abhishek Chopra-abhishekchop76@ibl-515310819699-CR VIA UPI | `573264582918` |
| 26/07/25 | Credit | NEFT*N59747919941/Deepak Pillai/CR | NEFT*N59747919941/Deepak Pillai/CR | `833738278606` |
| 26/07/25 | Credit | NEFT*N23765562926/Pallavi Verma/CR | NEFT*N23765562926/Pallavi Verma/CR | `890636500388` |
| 27/07/25 | Credit/Debit | RTGS-R67993657544-Girish Sethi/BDBL0345407 | RTGS-R67993657544-Girish Sethi/BDBL0345407 | `728297967785` |

### Pattern 4 — Fund Pooling

**Severity:** HIGH  
**Pattern ID:** 4  
**Amount Range:** ₹29,400.01 – ₹70,900.79  
**Reason:** Fund pooling from multiple unrelated senders within a short window.  

**Accounts Involved:**

- **Mixed Subject** — THE FEDERAL BANK LIMITED, Account `06555427844681` (`06555427844681-01-12-2024to08-05-2026.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 30-06-2025 | Credit | UPI/CR/840806386509/Sneha/HDFC/sneha.singh@aubank/UPI | UPI/CR/840806386509/Sneha/HDFC/sneha.singh@aubank/UPI | `339965259099` |
| 28-06-2025 | Credit | UPI/CR/189435331126/Vishal/BKID/1333359482@oksbi/UPI | UPI/CR/189435331126/Vishal/BKID/1333359482@oksbi/UPI | `459953850768` |
| 30-06-2025 | Credit | UPI/CR/492457258257/Mukesh/BARB/mukeshkuma42@oksbi/UPI | UPI/CR/492457258257/Mukesh/BARB/mukeshkuma42@oksbi/UPI | `263317444575` |
| 29-06-2025 | Credit | UPI/CR/414537747204/Santosh/PUNB/santoshpand49@axl/UPI | UPI/CR/414537747204/Santosh/PUNB/santoshpand49@axl/UPI | `611519359760` |
| 29-06-2025 | Credit | UPI/CR/046120409939/Arun/HDFC/7442369848@ptsbi/UPI | UPI/CR/046120409939/Arun/HDFC/7442369848@ptsbi/UPI | `237695993693` |

### Pattern 5 — Structuring Smurfing

**Severity:** HIGH  
**Pattern ID:** 5  
**Amount Range:** ₹42,900.00 – ₹49,400.00  
**Reason:** Repeated cash deposits just below a common reporting threshold.  

**Accounts Involved:**

- **Mixed Subject** — BANK OF INDIA, Account `6369331266799686` (`6369331266799686-01-12-2024to09-05-2026.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| — | — | 42,900.00–49,400.00 | _(see statement)_ | `366373562330` |
| — | — | 42,900.00–49,400.00 | _(see statement)_ | `214460637165` |
| — | — | 42,900.00–49,400.00 | _(see statement)_ | `921958613104` |
| — | — | 42,900.00–49,400.00 | _(see statement)_ | `529630811842` |
| — | — | 42,900.00–49,400.00 | _(see statement)_ | `980049282762` |
| — | — | 42,900.00–49,400.00 | _(see statement)_ | `941251783724` |

### Pattern 7 — Circular Flow

**Severity:** HIGH  
**Pattern ID:** 7  
**Amount Range:** ₹350,207.88 – ₹360,000.00  
**Reason:** Closed-loop circular flow; every hop corroborated by both statements.  

**Accounts Involved:**

- **Mixed Subject** — THE FEDERAL BANK LIMITED, Account `55794792847269` (`55794792847269-01-12-2024to09-05-2026.pdf`)
- **Mixed Subject** — UCO BANK, Account `9454583674913372` (`9454583674913372-02-12-2024to09-05-2026.pdf`)
- **Mixed Subject** — BANK OF BARODA, Account `3185728472711726` (`3185728472711726-01-12-2024to09-05-2026.xlsx`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 21-07-2025 | Credit | 360,000.00 | RTGS/R91028908588/RANI MALHOTRA/UCBA0158521 | `R91028908588` |
| 22-07-2025 | Credit | 358,008.65 | 22-07-2025 NEFT/N13895095304/SANGITA MUKHERJEE | `N13895095304` |
| 23-07-2025 | Credit | 350,207.88 | IMPS/P2A/I35266963746//SANGITA MUKHERJE/BARB | `I35266963746` |

### Pattern 8 — Money Trail

**Severity:** HIGH  
**Pattern ID:** 8  
**Amount Range:** ₹267,978.56 – ₹304,759.12  
**Reason:** Multi-hop trail; real entries on both sides of every transfer.  

**Accounts Involved:**

- **Mixed Subject** — THE FEDERAL BANK LIMITED, Account `00837844971737` (`00837844971737-01-12-2024to09-05-2026.csv`)
- **Mixed Subject** — BANK OF INDIA, Account `3922181054742642` (`3922181054742642-01-12-2024to08-05-2026.xlsx`)
- **Mixed Subject** — BANK OF BARODA, Account `9791722953307803` (`9791722953307803-01-12-2024to09-05-2026.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 06-06-2025 | Credit/Debit | NEFT/N27110756706/BRIJESH YADAV | NEFT/N27110756706/BRIJESH YADAV | `N27110756706` |
| 07-06-2025 | Debit | 267,978.56 | IMPS-I82873386062-USHA AHUJA | `I82873386062` |

### Pattern 9 — Credit To Cash Out

**Severity:** HIGH  
**Pattern ID:** 9  
**Amount Range:** ₹136,868.86 – ₹147,000.06  
**Reason:** Large inward credit followed promptly by near-equivalent ATM withdrawal.  

**Accounts Involved:**

- **Mixed Subject** — PUNJAB NATIONAL BANK, Account `1157402870460715` (`1157402870460715_statement.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| — | — | 136,868.86–147,000.06 | _(see statement)_ | `400603066066` |
| — | — | 136,868.86–147,000.06 | _(see statement)_ | `769049702334` |

### Pattern 10 — Cross Statement Links

**Severity:** HIGH  
**Pattern ID:** 10  
**Amount:** ₹88,000.93  
**Reason:** Same bank reference appears on two independent account statements.  

**Accounts Involved:**

- **Mixed Subject** — UCO BANK, Account `2074341316704650` (`2074341316704650-01-12-2024to09-05-2026.xlsx`)
- **Mixed Subject** — STATE BANK OF INDIA, Account `64831176837` (`statement-64831176837.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 16-08-2025 | Debit | 88,000.93 | IMPS-I61606559645-PANKAJ CHAUDHARY | `I61606559645` |

### Pattern 11 — Balance Parking

**Severity:** HIGH  
**Pattern ID:** 11  
**Amount:** ₹361,000.17  
**Reason:** Large credit remains parked; subsequent activity is minor.  

**Accounts Involved:**

- **Mixed Subject** — BANDHAN BANK LIMITED, Account `49914742547252` (`49914742547252_SOA.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| — | — | ~361,000.17 | _(see statement)_ | `938904808455` |

### Pattern 12 — Hub Ranking

**Severity:** HIGH  
**Pattern ID:** 12  
**Amount Range:** ₹19,100.61 – ₹63,200.00  
**Reason:** Hub receives from 6-8 spoke accounts with corroborating statements.  

**Accounts Involved:**

- **Mixed Subject** — THE FEDERAL BANK LIMITED, Account `55794792847269` (`55794792847269-01-12-2024to09-05-2026.pdf`)
- **Mixed Subject** — UCO BANK, Account `9454583674913372` (`9454583674913372-02-12-2024to09-05-2026.pdf`)
- **Mixed Subject** — BANK OF BARODA, Account `3185728472711726` (`3185728472711726-01-12-2024to09-05-2026.xlsx`)
- **Mixed Subject** — THE FEDERAL BANK LIMITED, Account `00837844971737` (`00837844971737-01-12-2024to09-05-2026.csv`)
- **Mixed Subject** — BANK OF INDIA, Account `3922181054742642` (`3922181054742642-01-12-2024to08-05-2026.xlsx`)
- **Mixed Subject** — BANK OF BARODA, Account `9791722953307803` (`9791722953307803-01-12-2024to09-05-2026.csv`)
- **Mixed Subject** — PUNJAB NATIONAL BANK, Account `1157402870460715` (`1157402870460715_statement.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| — | — | 19,100.61–63,200.00 | _(see statement)_ | `U81240405564` |
| 08-09-2025 | Credit | 43,000.39 | IMPS/P2A/I73434873986//SANGITA MUKHERJE/BARB | `I73434873986` |
| 09-09-2025 | Credit | 56,000.70 | NEFT/N32270877907/YOGESH PATIL | `N32270877907` |
| 10-09-2025 | Credit | 19,100.61 | IMPS/P2A/I18014212366//BRIJESH YADAV/BKID | `I18014212366` |
| 07-09-2025 | Credit | 63,200.00 | IMPS/P2A/I38784067999//USHA AHUJA/BARB | `I38784067999` |
| 08-09-2025 | Credit | 36,200.56 | IMPS/P2A/I20081967062//HARISH KUMAR/PUNB | `I20081967062` |

### Pattern 13 — Low Value Testing

**Severity:** HIGH  
**Pattern ID:** 13  
**Amount Range:** ₹8.21 – ₹31.09  
**Reason:** Reciprocal low-value probes on both real account sides.  

**Accounts Involved:**

- **Mixed Subject** — BANDHAN BANK LIMITED, Account `26278416411428` (`26278416411428_SOA.pdf`)
- **Mixed Subject** — KOTAK MAHINDRA BANK LTD, Account `6912827621` (`6912827621_statement.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| — | — | 8.21–31.09 | _(see statement)_ | `U54388548058` |
| — | — | 8.21–31.09 | _(see statement)_ | `U04332109674` |
| — | — | 8.21–31.09 | _(see statement)_ | `U61346868591` |
| — | — | 8.21–31.09 | _(see statement)_ | `U49172343877` |
| — | — | 8.21–31.09 | _(see statement)_ | `U19618075118` |

### Pattern 14 — Reversal Clusters

**Severity:** HIGH  
**Pattern ID:** 14  
**Amount Range:** ₹6,200.06 – ₹35,700.24  
**Reason:** Repeated debit-reversal pattern across multiple cycles.  

**Accounts Involved:**

- **Mixed Subject** — HDFC BANK LTD, Account `99132894316457` (`99132894316457 statement.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 10/07/25 | Credit/Debit | UPI-Sapna Nambiar-sapna@paytm-201003027708-DR VIA UPI | UPI-Sapna Nambiar-sapna@paytm-201003027708-DR VIA UPI | `U76420001320` |
| 11/07/25 | Credit | RETURN/U76420001320/REVERSAL | RETURN/U76420001320/REVERSAL | `960886991339` |
| 13/07/25 | Credit/Debit | UPI-Sapna Srivastava-sapna@paytm-868726548898-DR VIA UPI | UPI-Sapna Srivastava-sapna@paytm-868726548898-DR VIA UPI | `U89027366023` |
| 14/07/25 | Credit | RETURN/U89027366023/REVERSAL | RETURN/U89027366023/REVERSAL | `532495746758` |
| 16/07/25 | Credit/Debit | UPI-Pankaj Thapar-pankaj@paytm-519526487462-DR VIA UPI | UPI-Pankaj Thapar-pankaj@paytm-519526487462-DR VIA UPI | `U34603953253` |
| 17/07/25 | Credit | RETURN/U34603953253/REVERSAL | RETURN/U34603953253/REVERSAL | `404328588115` |
| 19/07/25 | Credit/Debit | UPI-Renu Srivastava-renu@paytm-141693263838-DR VIA UPI | UPI-Renu Srivastava-renu@paytm-141693263838-DR VIA UPI | `U66218436408` |
| 20/07/25 | Credit | RETURN/U66218436408/REVERSAL | RETURN/U66218436408/REVERSAL | `611151012081` |
| 22/07/25 | Credit/Debit | UPI-Sarita Banerjee-sarita@paytm-526605459023-DR VIA UPI | UPI-Sarita Banerjee-sarita@paytm-526605459023-DR VIA UPI | `U79258957612` |
| 23/07/25 | Credit | RETURN/U79258957612/REVERSAL | RETURN/U79258957612/REVERSAL | `449540790370` |

### Pattern 15 — Round Value Debit

**Severity:** MEDIUM  
**Pattern ID:** 15  
**Amount Range:** ₹10,000.00 – ₹80,000.00  
**Reason:** Cluster of round-value outward transfers amid non-round routine spending.  

**Accounts Involved:**

- **Mixed Subject** — BANK OF INDIA, Account `6082267802022370` (`6082267802022370-01-12-2024to08-05-2026.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 15-05-2025 | Credit/Debit | NEFT/N00858836949/Ritu Chaudhary | NEFT/N00858836949/Ritu Chaudhary | `367404071386` |
| 17-05-2025 | Credit/Debit | NEFT/N48876190198/Ritu Chaudhary | NEFT/N48876190198/Ritu Chaudhary | `021061609074` |
| 19-05-2025 | Credit/Debit | NEFT/N51969513084/Ritu Chaudhary | NEFT/N51969513084/Ritu Chaudhary | `034073908374` |
| 21-05-2025 | Credit/Debit | NEFT/N47183235546/Ritu Chaudhary | NEFT/N47183235546/Ritu Chaudhary | `141682412773` |
| 23-05-2025 | Credit/Debit | NEFT/N95585118949/Ritu Chaudhary | NEFT/N95585118949/Ritu Chaudhary | `024146173538` |
| 25-05-2025 | Credit/Debit | NEFT/N03009767905/Ritu Chaudhary | NEFT/N03009767905/Ritu Chaudhary | `081258815661` |
| 27-05-2025 | Credit/Debit | NEFT/N04224740024/Ritu Chaudhary | NEFT/N04224740024/Ritu Chaudhary | `008017784954` |

### Pattern 16 — Shared Upi

**Severity:** HIGH  
**Pattern ID:** 16  
**Amount Range:** ₹1,430.49 – ₹7,750.45  
**Reason:** Handle naveen40@apl appears across separate account statements.  

**Accounts Involved:**

- **Mixed Subject** — UCO BANK, Account `2074341316704650` (`2074341316704650-01-12-2024to09-05-2026.xlsx`)
- **Mixed Subject** — STATE BANK OF INDIA, Account `64831176837` (`statement-64831176837.csv`)
- **Mixed Subject** — BANDHAN BANK LIMITED, Account `49914742547252` (`49914742547252_SOA.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 17-03-2025 | Debit | 6,820.55 | UPI/DR/971937312389/Common/FEDERAL/naveen40@apl/UPI | `578977542504` |
| 18-03-2025 | Debit | 7,750.45 | UPI/DR/218195812338/Common/HDFC/naveen40@apl/UPI | `287964137374` |
| — | — | 1,430.49–7,750.45 | _(see statement)_ | `079206095451` |

### Pattern 17 — Round Trip

**Severity:** HIGH  
**Pattern ID:** 17  
**Amount Range:** ₹252,156.19 – ₹286,000.89  
**Reason:** Out-and-back round-trip via different channels; all sides have statements.  

**Accounts Involved:**

- **Mixed Subject** — BANK OF BARODA, Account `0642911656685344` (`0642911656685344-01-12-2024to08-05-2026.csv`)
- **Mixed Subject** — BANK OF BARODA, Account `9592043503463703` (`9592043503463703-02-12-2024to09-05-2026.csv`)
- **Mixed Subject** — HDFC BANK LTD, Account `92626656155172` (`92626656155172 statement.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 10-08-2025 | Credit/Debit | NEFT/N34420581585/SAPNA PILLAI | NEFT/N34420581585/SAPNA PILLAI | `N34420581585` |
| 12-08-2025 | Credit/Debit | IMPS-I02224230004-LATA MUKHERJEE | IMPS-I02224230004-LATA MUKHERJEE | `I02224230004` |
| 16-08-2025 | Credit | RTGS/R48694250121/LATA MUKHERJEE/HDFC0833125 | RTGS/R48694250121/LATA MUKHERJEE/HDFC0833125 | `R48694250121` |

### Pattern 18 — Dormant Reactivation

**Severity:** HIGH  
**Pattern ID:** 18  
**Amount Range:** ₹3,640.70 – ₹288,000.26  
**Reason:** Long dormancy followed by a material reactivation burst.  

**Accounts Involved:**

- **Mixed Subject** — THE FEDERAL BANK LIMITED, Account `93649988897865` (`93649988897865-25-12-2024to04-11-2025.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| — | — | 3,640.70–288,000.26 | _(see statement)_ | `856434181988` |
| — | — | 3,640.70–288,000.26 | _(see statement)_ | `186580291181` |
| — | — | 3,640.70–288,000.26 | _(see statement)_ | `410317508133` |

### Pattern 19 — First Contact Large Transfer

**Severity:** HIGH  
**Pattern ID:** 19  
**Amount:** ₹266,000.20  
**Reason:** No prior relationship; first-ever contact is a large RTGS transfer.  

**Accounts Involved:**

- **Mixed Subject** — THE FEDERAL BANK LIMITED, Account `06555427844681` (`06555427844681-01-12-2024to08-05-2026.csv`)
- **Mixed Subject** — BANK OF INDIA, Account `6369331266799686` (`6369331266799686-01-12-2024to09-05-2026.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 28-02-2025 | Credit/Debit | RTGS/R42930926366/ASHISH MENON/BKID0967972 | RTGS/R42930926366/ASHISH MENON/BKID0967972 | `R42930926366` |

### Pattern 22 — Llm Lead Unknown Shape

**Severity:** LOW (Safety Net — no named rule match)  
**Pattern ID:** 22  
**Amount Range:** ₹1,901.27 – ₹9,174.06  
**Reason:** Expected zero strong/weak findings from Patterns 1-19; surface only via Pattern 22/23 safety-net trigger.  

**Accounts Involved:**

- **Mixed Subject** — AXIS BANK LIMITED, Account `940797593562472` (`940797593562472_statement.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 03-06-2025 | Credit | UPIP2A363351283977KunalKhannaUPIHDFC | UPIP2A363351283977KunalKhannaUPIHDFC | `882421277021` |
| 05-06-2025 | Credit/Debit | UPIP2M574314058455RaviMenonUPIBDBL | UPIP2M574314058455RaviMenonUPIBDBL | `790095633011` |
| 06-06-2025 | Credit/Debit | UPIP2M071561196245MayaDasUPIPUNB | UPIP2M071561196245MayaDasUPIPUNB | `338000686081` |
| 15-06-2025 | Credit | UPIP2A616864954683SeemaJoshiUPIUCBA | UPIP2A616864954683SeemaJoshiUPIUCBA | `666397895254` |
| 16-06-2025 | Credit/Debit | UPIP2M248565554839PreetiGhoshUPIPUNB | UPIP2M248565554839PreetiGhoshUPIPUNB | `293292066059` |
| 25-06-2025 | Credit/Debit | UPIP2M827736203020TarunKulkarnUPIBKID | UPIP2M827736203020TarunKulkarnUPIBKID | `638214467228` |
| 26-07-2025 | Credit | UPIP2A093785920165RajanIyerUPIHDFC | UPIP2A093785920165RajanIyerUPIHDFC | `338278647271` |

### Pattern 23 — Ml Ensemble Unknown Shape

**Severity:** LOW (Safety Net — no named rule match)  
**Pattern ID:** 23  
**Amount Range:** ₹697.73 – ₹9,692.76  
**Reason:** Expected zero strong/weak findings from Patterns 1-19; surface only via Pattern 22/23 safety-net trigger.  

**Accounts Involved:**

- **Mixed Subject** — PUNJAB NATIONAL BANK, Account `9824732161017095` (`9824732161017095_statement.txt`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 10-06-2025 | Credit | 5,548.64 | UPI/CR/123642935197/Varsha/BARB/varsha596@aubank/U | `161022627830` |
| 12-06-2025 | Debit | 6,353.13 | UPI/DR/120048028643/Lata/PUNB/1226888741@pthdfc/UP | `866384252195` |
| 29-06-2025 | Debit | 9,692.76 | UPI/DR/994144282112/Meena/KKBK/meena161@ybl/UPI | `316022545800` |
| 30-06-2025 | Credit | 2,118.35 | UPI/CR/845815588618/Suresh/SBIN/suresh.gupta@ptaxi | `402434421353` |
| 09-07-2025 | Debit | 2,020.16 | UPI/DR/618631632611/Shivam/BDBL/7825610442@ybl/UPI | `940015372862` |
| 09-08-2025 | Debit | 5,877.78 | UPI/DR/079259445673/Abhishek/KKBK/abhishek288@ybl/ | `842605296236` |
| 21-09-2025 | Credit | 3,007.08 | UPI/CR/980396882800/Naresh/UTIB/nareshdas87@apl/UP | `111343714506` |
| 08-10-2025 | Debit | 5,016.21 | UPI/DR/541456962074/Lata/FDRL/lata.sethi@ybl/UPI | `418451656961` |
| 10-10-2025 | Debit | 697.73 | UPI/DR/581862290035/Girish/KKBK/girish.dutta@kotak | `771851106316` |
| 10-11-2025 | Credit | 8,376.04 | UPI/CR/108322769529/Anil/FDRL/anil489@ptyes/UPI | `041333853405` |

## Expected Non-Findings

The following pattern detectors must NOT trigger on this dataset:

| Pattern ID | Pattern Name | Reason |
|-----------|--------------|--------|

## Validation Notes

To manually verify this ground truth:

1. Open each statement file listed in **Dataset Files** above.
2. Search for each **Reference / UTR** value in the reference/narration columns.
3. Confirm the transaction date, amount, and type match the values above.
4. Confirm no other pattern detector fires on accounts listed as clean controls.
5. Dataset seed: `2025` — re-running the generator with this seed reproduces identical files.

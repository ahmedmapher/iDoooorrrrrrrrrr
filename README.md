## Story
The app was "modernized" to use UUIDs and proper checks. However, *legacy* features still exist.

- Flag format: `flag{...}`
- Difficulty: Medium
- Category: Web / Access Control

## Run
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:8000

## Credentials
- `ahmed / oppenheimer`  (intended player)

## Hints (optional to give players)
- Base64 isn't a signature.
- UI restrictions are not authorization.
- UUID routes can be secure while legacy paths remain vulnerable.
- Musk's invoices have the treasure

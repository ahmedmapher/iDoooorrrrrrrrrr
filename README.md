# Neighborly Invoices — IDOR CTF
A tiny Flask web app intentionally vulnerable to **IDOR (Insecure Direct Object Reference)**.

## Story
You have access to a small invoicing portal as **Alice**. Another tenant, **Bob**, also has invoices in the system. Can you find a way to view **Bob's** invoice and capture the flag?

- Flag format: `FLAG{...}`
- Difficulty: Easy
- Category: Web / Access Control / IDOR

## Quick Start (no Docker)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:8000

## Quick Start (Docker)
```bash
docker build -t idor-ctf .
docker run --rm -p 8000:8000 idor-ctf
```
Open http://127.0.0.1:8000

## Credentials
- Username: `alice`
- Password: `wonderland`

(*There is also a user `bob` with password `builder`, but that account is not needed to solve the challenge.*)

## Objective
Log in as Alice and view **Bob's** invoice to find the flag.

## Rules for players
- Attack only this local container/app.
- Do not brute force; the point is access control, not guessing passwords.
- Have fun and learn!

## Organizer Notes
- The vulnerable route is `/invoice?id=<number>` and `/api/invoice?id=<number>`
- The fix is shown in `/secure/invoice` where ownership is enforced.
- To change the flag, edit the `notes` field of Bob's invoice in `app.py`.

# Stellar Account as a Service - Django version

Implements the [Stellar Account as a Service bounty](https://github.com/tyvdh/stellar-quest-bounties/blob/main/bounties/level-2/stellar-accounts-as-a-service.md) in Django with Django Rest Framework

## Requirements

### Environment Variables

- `ENABLE_SEP_0023=True`: mandatory for Stellar SDK support of muxed accounts
- `DEBUG`: defaults to False
- `ALLOWED_HOSTS`: defaults to localhost
- `STATIC_ROOT`: static folder when running in prod
- `DJANGO_SECRET_KEY`: mandatory
- `STELLAR_SERVER`: defaults to https://horizon-testnet.stellar.org
- `VAULT_PUBLIC_KEY`: mandatory
- `VAULT_SECRET_KEY`: mandatory

## How to run

### Setup

Install requirements:

```shell
pip install -r requirements.txt
```

Initialize the db:

```shell
cd saas
python manage.py migrate
```

### Running the app

The app is made of two parts:
- a Django Rest Framework API
- a watcher daemon that streams payment from the Stellar Network to find incoming payments and update the balances

#### Django web app

Run the app normally:

```shell
python manage runserver localhost:8000
```

But best to run it with HTTPS, see [mkcert](https://github.com/FiloSottile/mkcert) for getting local trusted certs:

```shell
brew install mkcert
mkcert -install
# In the Django folder
mkcert localhost
python manage.py runsslserver localhost:8000 --certificate localhost.pem --key localhost-key.pem
```

#### Watcher daemon

The watcher was implemented as a Django management command that must be run continuously:

```shell
python manage.py watch_payments
```

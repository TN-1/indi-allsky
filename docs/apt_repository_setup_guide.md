# APT Repository Setup Guide (GitHub Pages & GitHub Actions)

This guide walks through setting up an official **APT Repository** hosted for free on **GitHub Pages** and automatically updated via **GitHub Actions**.

With an APT repository configured, users can install and update `indi-allsky` and pre-compiled INDI drivers on Raspberry Pi OS, Debian, Ubuntu, Astroberry, and StellarMate using standard `apt`:

```bash
sudo apt update && sudo apt install indi-allsky
```

---

## Architecture Overview

```mermaid
flowchart LR
    A[Git Release Tag / Nightly Cron] --> B[GitHub Actions Runner]
    B --> C[Build Multi-Arch .deb Matrix]
    C --> D[Index Packages into reprepro: main & nightly]
    D --> E[Sign with GPG Key]
    E --> F[Deploy to GitHub Pages via actions/deploy-pages]
    F --> G[HTTPS Web Host: your-repo.github.io]
    G --> H[Raspberry Pi / Debian / Ubuntu Clients via apt]
```

---

## Step 1: Generate GPG Signing Key

The APT repository metadata (`Release` / `InRelease` file) is cryptographically signed using GPG so `apt` verifies package authenticity.

On your local machine, generate an RSA 4096-bit GPG key (with `%no-protection` so it can sign packages unattended in GitHub Actions CI/CD):

```bash
gpg --batch --gen-key <<EOF
%no-protection
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: INDI Allsky Repository
Name-Email: <your-email-here>
Expire-Date: 0
EOF
```

List your secret keys to find your Key ID:

```bash
gpg --list-secret-keys --keyid-format LONG
```
*(Look for the string after `rsa4096/`, e.g. `sec rsa4096/3AA5C34371567BD2`).*

---

## Step 2: Configure GitHub Repository Secrets

Export your private key:

```bash
# Export using your Key ID or Email
gpg --armor --export-secret-keys <YOUR_KEY_ID_OR_EMAIL>
```

1. Navigate to your repository on GitHub: **Settings** -> **Secrets and variables** -> **Actions**.
2. Click **New repository secret**.
3. Add secret:
   - **Name**: `GPG_PRIVATE_KEY`
   - **Value**: Paste the exported GPG private key block (including `-----BEGIN PGP PRIVATE KEY BLOCK-----`).

---

## Step 3: Enable GitHub Pages

1. Go to repository **Settings** -> **Pages**.
2. Under **Build and deployment**:
   - **Source**: Select **`GitHub Actions`** (do not select *Deploy from a branch*).
3. *(Optional Custom Domain)*: Enter your custom domain (e.g. `apt.indi-allsky.org`) and enable **Enforce HTTPS**.

---

## Step 4: Workflow Permissions & Environments

1. Go to repository **Settings** -> **Actions** -> **General**.
2. Scroll to **Workflow permissions**:
   - Select **Read and write permissions**.
   - Check **Allow GitHub Actions to create and approve pull requests**.
3. Click **Save**.

The workflow uses GitHub Pages environment deployment (`environment: github-pages`) with `id-token: write` and `pages: write` permissions automatically.

---

## Step 5: Automatic Workflow Integration

The deployment job (`deploy-apt-repo`) in [`.github/workflows/package-deb.yml`](../.github/workflows/package-deb.yml) automatically:
* Runs on tagged releases (`indi_v*`) and scheduled nightly builds (`02:00 UTC`).
* Maintains Debian suites for **Debian 12 (`bookworm`)**, **Debian 13 (`trixie`)**, and **Ubuntu 24.04 (`noble`)**.
* Maintains two distinct package channels:
  - **`main`**: Tested, stable tagged releases.
  - **`nightly`**: Bleeding-edge development builds generated from `main`.
* Packages and signs the repository using `reprepro` and publishes it to GitHub Pages with standard `actions/deploy-pages@v4`.

---

## Step 6: End-User Installation Instructions

Share these instructions with end-users to add your APT repository:

### 1. Add GPG Keyring & Repository Source (DEB822 Format)

#### Stable Channel (Recommended)
```bash
# Add Keyring
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://<your-username>.github.io/indi-allsky/key.gpg | sudo gpg --dearmor -o /etc/apt/keyrings/indi-allsky.gpg
sudo chmod a+r /etc/apt/keyrings/indi-allsky.gpg

# Add Sources (DEB822)
sudo tee /etc/apt/sources.list.d/indi-allsky.sources <<EOF
Types: deb
URIs: https://<your-username>.github.io/indi-allsky
Suites: $(lsb_release -cs)
Components: main
Signed-By: /etc/apt/keyrings/indi-allsky.gpg
EOF
```

#### Nightly Channel
```bash
# Add Keyring
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://<your-username>.github.io/indi-allsky/key.gpg | sudo gpg --dearmor -o /etc/apt/keyrings/indi-allsky.gpg
sudo chmod a+r /etc/apt/keyrings/indi-allsky.gpg

# Add Sources (DEB822)
sudo tee /etc/apt/sources.list.d/indi-allsky-nightly.sources <<EOF
Types: deb
URIs: https://<your-username>.github.io/indi-allsky
Suites: $(lsb_release -cs)
Components: nightly
Signed-By: /etc/apt/keyrings/indi-allsky.gpg
EOF
```

### 2. Install & Update
```bash
sudo apt update
sudo apt install -y indi-allsky
```

To update `indi-allsky` in the future:
```bash
sudo apt update && sudo apt upgrade
```

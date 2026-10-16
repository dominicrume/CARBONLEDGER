# Publishing CarbonLedger to the Solana dApp Store (Seeker)

The app is a Progressive Web App: carbonledger.world serves a manifest (`/manifest.webmanifest`), a service worker
(`/sw.js`) and installable icons. Chrome reports no installability errors (checked 2026-10-13). The dApp Store takes a
PWA wrapped as an Android app (a Trusted Web Activity), built with Bubblewrap. Source: docs.solanamobile.com,
"Publishing a PWA". Do these steps on your own machine: they create a signing key and spend SOL.

## 1. Build the Android app (once, then for each release)
```
npm i -g @bubblewrap/cli                       # Node 14.15 or newer; no sudo
mkdir -p ~/carbonledger-seeker && cd ~/carbonledger-seeker
bubblewrap init --manifest https://carbonledger.world/manifest.webmanifest
#   Domain: carbonledger.world   Start URL: /app#shop   Package id: world.carbonledger.app
#   Let it install the JDK and Android SDK. It creates android.keystore: back it up somewhere safe.
#   Losing the keystore or its password means the app can never be updated.
bubblewrap build                               # app-release-signed.apk
bubblewrap fingerprint generateAssetLinks      # writes assetlinks.json for your key
```
The keystore never goes in this repository (`*.keystore` and `*.jks` are in .gitignore).

## 2. Prove the app and the site belong together (Digital Asset Links)
Copy the generated `assetlinks.json` to `apps/web/.well-known/assetlinks.json`, commit it (it holds only the public
fingerprint), deploy, and check https://carbonledger.world/.well-known/assetlinks.json. Without it the app shows a
browser bar at the top instead of running full screen.

## 3. Submit to the dApp Store
Follow docs.solanamobile.com "Submit a dApp": the `dapp-store` CLI with a `config.yaml` (name, description, icon,
screenshots, the APK), then mint the publisher, app and release NFTs with a funded publisher wallet (mainnet SOL,
a human step) and submit for review. Read the Solana dApp Store publisher policy first.

## Listing copy (claims follow rules/HARDENING-PRODUCT.md)
- Short: "Retire pilot units to the gram and clear the world together. Every receipt checkable on Solana devnet."
- Always add: "Pilot units, not yet verified credits. No payment is taken."
- Never: "offset", "carbon neutral", "earn", "airdrop", or any SKR or token reward.

## Sign in with Seeker (built 2026-10-16)
On Android the app offers "Sign in with Seeker": Mobile Wallet Adapter (vendor/seeker-mwa-0.7.0.min.js, rebuilt by
scripts/build_seeker_mwa.sh) asks the Seed Vault wallet to sign one Sign-in-with-Solana message for carbonledger.world.
The server checks the signature, the domain and a one-time nonce, then reads mainnet (SOLANA_MAINNET_RPC_URL) for a
Seeker Genesis Token: a Token-2022 mint in group GT22s89nU4iWFkNXj1Bw6uYhJJWDRPpShHt4Bk8f99Te. One token marks one
account. The perk is a Seeker badge on the league and in the account; never tokens or money. Test it on a real Seeker:
there is no Genesis Token on devnet.

#!/usr/bin/env bash
# Rebuilds apps/web/vendor/seeker-mwa-0.7.0.min.js: Mobile Wallet Adapter for the web, bundled once so the app keeps
# no build step and every script stays pinned with an integrity hash (D7). The only use: the Seeker wallet signs one
# sign-in message. No transactions. After rebuilding, update SEEKER_MWA in apps/web/js/core/account.js with
# scripts/vendor_hashes.sh. Pinned: @solana-mobile/wallet-standard-mobile 0.7.0, @wallet-standard/app 1.1.1, esbuild 0.28.2.
set -euo pipefail
OUT="$(cd "$(dirname "$0")/.." && pwd)/apps/web/vendor/seeker-mwa-0.7.0.min.js"
W="$(mktemp -d)"; cd "$W"
npm init -y >/dev/null
npm install --silent --save-exact @solana-mobile/wallet-standard-mobile@0.7.0 @wallet-standard/app@1.1.1 esbuild@0.28.2
cat > entry.js <<'EOF'
// CarbonLedger's only use of Mobile Wallet Adapter: let the Seeker's wallet sign one sign-in message. No transactions.
import { registerMwa, createDefaultAuthorizationCache, createDefaultChainSelector, createDefaultWalletNotFoundHandler } from '@solana-mobile/wallet-standard-mobile';
import { getWallets } from '@wallet-standard/app';
let done = false;
const b64 = (u8) => btoa(String.fromCharCode(...u8));
window.CarbonLedgerSeeker = {
  register(identity) {
    if (done) return; done = true;
    registerMwa({ appIdentity: identity, authorizationCache: createDefaultAuthorizationCache(), chains: ['solana:mainnet'],
      chainSelector: createDefaultChainSelector(), onWalletNotFound: createDefaultWalletNotFoundHandler() });
  },
  available() { return getWallets().get().some(w => w.features['solana:signIn']); },
  // input: the server's challenge (domain, statement, uri, nonce, issuedAt, expirationTime). Returns base64 parts.
  async signIn(input) {
    const w = getWallets().get().find(x => x.features['solana:signIn']);
    if (!w) throw new Error('No Seeker wallet found in this browser.');
    const [out] = await w.features['solana:signIn'].signIn({ ...input, chainId: 'solana:mainnet' });
    return { address: out.account.address, signed_message: b64(out.signedMessage), signature: b64(out.signature) };
  },
};
EOF
npx esbuild entry.js --bundle --minify --format=iife --platform=browser --target=chrome100 --legal-comments=eof --outfile="$OUT"
echo "built $OUT"

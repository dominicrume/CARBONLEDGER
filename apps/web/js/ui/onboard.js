// First visit: three steps and one button, then straight into the game. Shown once per browser.
import { store } from '../core/store.js';
import { sheet } from './dom.js';
import { icon, brandMark } from './hud.js';

export function maybeOnboard(go) {
  if (store.get('onboarded', false)) return;
  sheet(`
    <div class="onboard">
      ${brandMark(56, 'onboard-mark')}
      <p class="eyebrow">You are in the CarbonLedger app</p>
      <h2 class="sheet-title">Every gram you retire moves the world</h2>
      <ol class="onboard-steps">
        <li>${icon('basket')}<div><strong>Scan or log</strong><small>A basket, a journey or a day. We work out the carbon from cited sources.</small></div></li>
        <li>${icon('leaf')}<div><strong>Retire pilot units</strong><small>One gram is one point. Level up, earn badges, keep a weekly streak.</small></div></li>
        <li>${icon('globe')}<div><strong>Clear the world together</strong><small>Everyone's retirements clear the smallest country first. Every receipt is checkable on Solana devnet.</small></div></li>
      </ol>
      <p class="note">Pilot units recorded on Solana devnet. Not yet verified credits. No payment is taken. The logo at the top takes you back to the website.</p>
      <div class="row"><button class="btn ghost" data-close id="onboard-skip">Look around</button><button class="btn primary" data-close id="onboard-go">${icon('basket')} Start with a basket</button></div>
    </div>`, { onOpen: (root) => {
      store.set('onboarded', true);            // shown once, however it is closed (button, scrim or Escape)
      root.querySelector('#onboard-go').addEventListener('click', () => { go('shop'); setTimeout(() => document.querySelector('#shelf-btn')?.click(), 250); });
    } });
}

// STATUS: NOT COMPILED OR TESTED. No Rust toolchain was available where this was written (2026-10-11 revision).
// The rules mirror packages/core/carbonledger/registry.py, which IS tested. Before trusting this file:
//   1. `anchor build` and fix any compile errors,
//   2. replay conformance/registry_vectors.json against it (programs/carbon_registry/tests/conformance.ts),
//   3. only then deploy to devnet. Mainnet needs an independent review and multisig keys.
// Units are grams. 1 CLT = 1 tonne = 1,000,000 grams.
//
// Design for volume (SCALING.md item 2, D15): there is NO per-retirement account. Retirements are recorded by the
// API in its receipt chain, and a Merkle root over many receipts is anchored in one `anchor_root` instruction per
// interval. What stays on-chain per entity: the registry, each project, each batch (the hot counters), each linked
// external credit (the anti double-count rule, which must be unique across parties) and each anchor.
use anchor_lang::prelude::*;

declare_id!("3dGd2V1ykcmahyCQvhri4R2WhabT83hmm2WNz2r788Zj"); // replace with the real id from `anchor keys list`

pub const MAX_VERIFIERS: usize = 3;

#[program]
pub mod carbon_registry {
    use super::*;

    pub fn initialize_registry(ctx: Context<InitializeRegistry>, verifier: Pubkey, attest_two_above_g: u64) -> Result<()> {
        let r = &mut ctx.accounts.registry;
        r.authority = ctx.accounts.authority.key();
        r.verifiers = [verifier, Pubkey::default(), Pubkey::default()];
        r.verifier_count = 1;
        r.attest_two_above_g = attest_two_above_g;
        r.bump = ctx.bumps.registry;
        Ok(())
    }

    // Up to three verifiers. Adding and rotating is the authority's job; attesting is theirs alone.
    pub fn add_verifier(ctx: Context<AuthorityOnly>, verifier: Pubkey) -> Result<()> {
        let r = &mut ctx.accounts.registry;
        require!((r.verifier_count as usize) < MAX_VERIFIERS, RegistryError::TooManyVerifiers);
        require!(!r.verifiers.contains(&verifier), RegistryError::Exists);
        let slot = r.verifier_count as usize;
        r.verifiers[slot] = verifier;
        r.verifier_count += 1;
        Ok(())
    }

    pub fn rotate_verifier(ctx: Context<AuthorityOnly>, old: Pubkey, new: Pubkey) -> Result<()> {
        let r = &mut ctx.accounts.registry;
        require!(!r.verifiers.contains(&new), RegistryError::Exists);
        let slot = r.verifiers.iter().position(|v| *v == old).ok_or(RegistryError::Unauthorised)?;
        r.verifiers[slot] = new;
        Ok(())
    }

    pub fn register_project(ctx: Context<RegisterProject>, project_id: u64, country: [u8; 3], methodology: [u8; 16]) -> Result<()> {
        let p = &mut ctx.accounts.project;
        p.project_id = project_id;
        p.country = country;
        p.methodology = methodology;
        p.status = ProjectStatus::Proposed;
        p.attested_g = 0;
        p.issued_g = 0;
        p.pending_attest_g = 0;
        p.pending_attest_by = Pubkey::default();
        p.bump = ctx.bumps.project;
        Ok(())
    }

    // Only a verifier named in the registry can attest. Attestation can rise but never fall below what is issued.
    // Above `attest_two_above_g`, the first call records a pending attestation and a second, different verifier
    // must repeat the same amount to make it stand (T4: one stolen verifier key cannot attest a large amount).
    pub fn attest_project(ctx: Context<AttestProject>, attested_g: u64) -> Result<()> {
        require!(attested_g > 0, RegistryError::BadAmount);
        let r = &ctx.accounts.registry;
        let signer = ctx.accounts.verifier.key();
        require!(r.is_verifier(&signer), RegistryError::Unauthorised);
        let p = &mut ctx.accounts.project;
        require!(p.status != ProjectStatus::Suspended, RegistryError::Suspended);
        require!(attested_g >= p.issued_g, RegistryError::OverIssuance);
        if attested_g > r.attest_two_above_g {
            if p.pending_attest_g == attested_g && p.pending_attest_by != signer && p.pending_attest_by != Pubkey::default() {
                p.pending_attest_g = 0;
                p.pending_attest_by = Pubkey::default();
            } else {
                p.pending_attest_g = attested_g;
                p.pending_attest_by = signer;
                return Ok(()); // recorded, not yet standing: a second verifier must agree
            }
        }
        p.attested_g = attested_g;
        p.status = ProjectStatus::Attested;
        Ok(())
    }

    // Nothing is issued unless attested, and issued never exceeds attested.
    pub fn issue_batch(ctx: Context<IssueBatch>, batch_id: u64, vintage: u16, grams: u64) -> Result<()> {
        require!(grams > 0, RegistryError::BadAmount);
        let p = &mut ctx.accounts.project;
        require!(p.status != ProjectStatus::Suspended, RegistryError::Suspended);
        require!(p.status == ProjectStatus::Attested, RegistryError::NotAttested);
        let total = p.issued_g.checked_add(grams).ok_or(RegistryError::Overflow)?;
        require!(total <= p.attested_g, RegistryError::OverIssuance);
        p.issued_g = total;
        let b = &mut ctx.accounts.batch;
        b.project = p.key();
        b.batch_id = batch_id;
        b.vintage = vintage;
        b.issued_g = grams;
        b.retired_g = 0;
        b.next_serial = 0;
        b.bump = ctx.bumps.batch;
        Ok(())
    }

    // The link account is a PDA from (registry name, serial) hashed off-chain. `init` fails if it exists,
    // so the same external credit can never be linked twice. That is the anti double-counting rule.
    pub fn link_external_credit(ctx: Context<LinkExternalCredit>, _key: [u8; 32]) -> Result<()> {
        ctx.accounts.link.batch = ctx.accounts.batch.key();
        ctx.accounts.link.bump = ctx.bumps.link;
        Ok(())
    }

    pub fn suspend_project(ctx: Context<ProjectAuthority>) -> Result<()> {
        ctx.accounts.project.status = ProjectStatus::Suspended;
        Ok(())
    }

    // Lifting a suspension returns the project to Attested only if it was attested; otherwise Proposed.
    pub fn unsuspend_project(ctx: Context<ProjectAuthority>) -> Result<()> {
        let p = &mut ctx.accounts.project;
        require!(p.status == ProjectStatus::Suspended, RegistryError::NotSuspended);
        p.status = if p.attested_g > 0 { ProjectStatus::Attested } else { ProjectStatus::Proposed };
        Ok(())
    }

    // The API retires on behalf of its callers. It takes a fresh serial range from the batch's hot counter.
    // No per-retirement account: the receipts live in the API's chain and are anchored by Merkle root below.
    pub fn retire(ctx: Context<Retire>, grams: u64) -> Result<(u64, u64)> {
        require!(grams > 0, RegistryError::BadAmount);
        require!(ctx.accounts.project.status != ProjectStatus::Suspended, RegistryError::Suspended);
        let b = &mut ctx.accounts.batch;
        let left = b.issued_g.checked_sub(b.retired_g).ok_or(RegistryError::Overflow)?;
        require!(grams <= left, RegistryError::OverRetirement);
        let start = b.next_serial;
        let end = start.checked_add(grams).ok_or(RegistryError::Overflow)?;
        b.next_serial = end;
        b.retired_g = b.retired_g.checked_add(grams).ok_or(RegistryError::Overflow)?;
        Ok((start, end))
    }

    // One anchor per interval: the Merkle root over receipt hashes [first_index, last_index]. The PDA is seeded by
    // first_index, so an interval can be anchored once, and intervals must be contiguous with the previous anchor.
    pub fn anchor_root(ctx: Context<AnchorRoot>, first_index: u64, last_index: u64, root: [u8; 32]) -> Result<()> {
        require!(last_index >= first_index, RegistryError::BadAmount);
        let r = &mut ctx.accounts.registry;
        require!(first_index == r.next_anchor_index, RegistryError::AnchorGap);
        let a = &mut ctx.accounts.anchor;
        a.first_index = first_index;
        a.last_index = last_index;
        a.root = root;
        a.slot = Clock::get()?.slot;
        a.bump = ctx.bumps.anchor;
        r.next_anchor_index = last_index + 1;
        Ok(())
    }
}

impl Registry {
    pub fn is_verifier(&self, key: &Pubkey) -> bool {
        self.verifiers.iter().take(self.verifier_count as usize).any(|v| v == key)
    }
}

#[derive(Accounts)]
pub struct InitializeRegistry<'info> {
    #[account(init, payer = authority, space = 8 + Registry::INIT_SPACE, seeds = [b"registry"], bump)]
    pub registry: Account<'info, Registry>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct AuthorityOnly<'info> {
    #[account(mut, seeds = [b"registry"], bump = registry.bump)]
    pub registry: Account<'info, Registry>,
    #[account(address = registry.authority @ RegistryError::Unauthorised)]
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
#[instruction(project_id: u64)]
pub struct RegisterProject<'info> {
    #[account(seeds = [b"registry"], bump = registry.bump)]
    pub registry: Account<'info, Registry>,
    #[account(init, payer = authority, space = 8 + Project::INIT_SPACE, seeds = [b"project", project_id.to_le_bytes().as_ref()], bump)]
    pub project: Account<'info, Project>,
    #[account(mut, address = registry.authority @ RegistryError::Unauthorised)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct AttestProject<'info> {
    #[account(seeds = [b"registry"], bump = registry.bump)]
    pub registry: Account<'info, Registry>,
    #[account(mut, seeds = [b"project", project.project_id.to_le_bytes().as_ref()], bump = project.bump)]
    pub project: Account<'info, Project>,
    pub verifier: Signer<'info>,
}

#[derive(Accounts)]
#[instruction(batch_id: u64)]
pub struct IssueBatch<'info> {
    #[account(seeds = [b"registry"], bump = registry.bump)]
    pub registry: Account<'info, Registry>,
    #[account(mut, seeds = [b"project", project.project_id.to_le_bytes().as_ref()], bump = project.bump)]
    pub project: Account<'info, Project>,
    #[account(init, payer = authority, space = 8 + Batch::INIT_SPACE, seeds = [b"batch", project.key().as_ref(), batch_id.to_le_bytes().as_ref()], bump)]
    pub batch: Account<'info, Batch>,
    #[account(mut, address = registry.authority @ RegistryError::Unauthorised)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(key: [u8; 32])]
pub struct LinkExternalCredit<'info> {
    #[account(seeds = [b"registry"], bump = registry.bump)]
    pub registry: Account<'info, Registry>,
    pub batch: Account<'info, Batch>,
    #[account(init, payer = authority, space = 8 + LinkedCredit::INIT_SPACE, seeds = [b"link", key.as_ref()], bump)]
    pub link: Account<'info, LinkedCredit>,
    #[account(mut, address = registry.authority @ RegistryError::Unauthorised)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct ProjectAuthority<'info> {
    #[account(seeds = [b"registry"], bump = registry.bump)]
    pub registry: Account<'info, Registry>,
    #[account(mut, seeds = [b"project", project.project_id.to_le_bytes().as_ref()], bump = project.bump)]
    pub project: Account<'info, Project>,
    #[account(address = registry.authority @ RegistryError::Unauthorised)]
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct Retire<'info> {
    #[account(seeds = [b"registry"], bump = registry.bump)]
    pub registry: Account<'info, Registry>,
    #[account(seeds = [b"project", project.project_id.to_le_bytes().as_ref()], bump = project.bump)]
    pub project: Account<'info, Project>,
    #[account(mut, constraint = batch.project == project.key() @ RegistryError::UnknownBatch)]
    pub batch: Account<'info, Batch>,
    // The API's hot key, named as the registry's operator. Callers never sign on-chain; the API retires for them.
    #[account(address = registry.authority @ RegistryError::Unauthorised)]
    pub operator: Signer<'info>,
}

#[derive(Accounts)]
#[instruction(first_index: u64)]
pub struct AnchorRoot<'info> {
    #[account(mut, seeds = [b"registry"], bump = registry.bump)]
    pub registry: Account<'info, Registry>,
    #[account(init, payer = operator, space = 8 + Anchor::INIT_SPACE, seeds = [b"anchor", first_index.to_le_bytes().as_ref()], bump)]
    pub anchor: Account<'info, Anchor>,
    #[account(mut, address = registry.authority @ RegistryError::Unauthorised)]
    pub operator: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
#[derive(InitSpace)]
pub struct Registry { pub authority: Pubkey, pub verifiers: [Pubkey; 3], pub verifier_count: u8, pub attest_two_above_g: u64, pub next_anchor_index: u64, pub bump: u8 }

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace)]
pub enum ProjectStatus { Proposed, Attested, Suspended }

#[account]
#[derive(InitSpace)]
pub struct Project { pub project_id: u64, pub country: [u8; 3], pub methodology: [u8; 16], pub status: ProjectStatus, pub attested_g: u64, pub issued_g: u64,
                     pub pending_attest_g: u64, pub pending_attest_by: Pubkey, pub bump: u8 }

#[account]
#[derive(InitSpace)]
pub struct Batch { pub project: Pubkey, pub batch_id: u64, pub vintage: u16, pub issued_g: u64, pub retired_g: u64, pub next_serial: u64, pub bump: u8 }

#[account]
#[derive(InitSpace)]
pub struct LinkedCredit { pub batch: Pubkey, pub bump: u8 }

#[account]
#[derive(InitSpace)]
pub struct Anchor { pub first_index: u64, pub last_index: u64, pub root: [u8; 32], pub slot: u64, pub bump: u8 }

// Names match the error codes in conformance/registry_vectors.json.
#[error_code]
pub enum RegistryError {
    #[msg("UNAUTHORISED")] Unauthorised,
    #[msg("NOT_ATTESTED")] NotAttested,
    #[msg("OVER_ISSUANCE")] OverIssuance,
    #[msg("OVER_RETIREMENT")] OverRetirement,
    #[msg("BAD_AMOUNT")] BadAmount,
    #[msg("SUSPENDED")] Suspended,
    #[msg("NOT_SUSPENDED")] NotSuspended,
    #[msg("UNKNOWN_BATCH")] UnknownBatch,
    #[msg("OVERFLOW")] Overflow,
    #[msg("EXISTS")] Exists,
    #[msg("TOO_MANY_VERIFIERS")] TooManyVerifiers,
    #[msg("ANCHOR_GAP")] AnchorGap,
}

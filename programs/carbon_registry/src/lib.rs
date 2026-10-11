// STATUS: NOT COMPILED OR TESTED IN THE SANDBOX THAT WROTE IT. No Rust toolchain was available.
// The rules below mirror packages/core/carbonledger/registry.py, which IS tested. Before trusting this file:
//   1. `anchor build` and fix any compile errors,
//   2. replay conformance/registry_vectors.json against it (see README.md in this folder),
//   3. only then deploy to devnet.
// Units are grams. 1 CLT = 1 tonne = 1,000,000 grams.
use anchor_lang::prelude::*;

declare_id!("11111111111111111111111111111111"); // replace with the real id from `anchor keys list`

#[program]
pub mod carbon_registry {
    use super::*;

    pub fn initialize_registry(ctx: Context<InitializeRegistry>, verifier: Pubkey) -> Result<()> {
        let r = &mut ctx.accounts.registry;
        r.authority = ctx.accounts.authority.key();
        r.verifier = verifier;
        r.bump = ctx.bumps.registry;
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
        p.bump = ctx.bumps.project;
        Ok(())
    }

    // Only the verifier named in the registry can attest. Attestation can rise but never fall below what is issued.
    pub fn attest_project(ctx: Context<AttestProject>, attested_g: u64) -> Result<()> {
        require!(attested_g > 0, RegistryError::BadAmount);
        let p = &mut ctx.accounts.project;
        require!(p.status != ProjectStatus::Suspended, RegistryError::Suspended);
        require!(attested_g >= p.issued_g, RegistryError::OverIssuance);
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

    pub fn suspend_project(ctx: Context<SuspendProject>) -> Result<()> {
        ctx.accounts.project.status = ProjectStatus::Suspended;
        Ok(())
    }

    // Each retirement takes a fresh serial range. The Retirement PDA is seeded by batch and start serial,
    // so a range can be written once. A gram can never be retired twice.
    pub fn retire(ctx: Context<Retire>, grams: u64, target: [u8; 3], memo_hash: [u8; 32]) -> Result<()> {
        require!(grams > 0, RegistryError::BadAmount);
        require!(ctx.accounts.project.status != ProjectStatus::Suspended, RegistryError::Suspended);
        let b = &mut ctx.accounts.batch;
        let left = b.issued_g.checked_sub(b.retired_g).ok_or(RegistryError::Overflow)?;
        require!(grams <= left, RegistryError::OverRetirement);
        let start = b.next_serial;
        let end = start.checked_add(grams).ok_or(RegistryError::Overflow)?;
        b.next_serial = end;
        b.retired_g = b.retired_g.checked_add(grams).ok_or(RegistryError::Overflow)?;
        let r = &mut ctx.accounts.retirement;
        r.batch = b.key();
        r.retiree = ctx.accounts.retiree.key();
        r.grams = grams;
        r.serial_start = start;
        r.serial_end = end;
        r.target = target;
        r.memo_hash = memo_hash;
        r.slot = Clock::get()?.slot;
        r.bump = ctx.bumps.retirement;
        Ok(())
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
    #[account(address = registry.verifier @ RegistryError::Unauthorised)]
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
pub struct SuspendProject<'info> {
    #[account(seeds = [b"registry"], bump = registry.bump)]
    pub registry: Account<'info, Registry>,
    #[account(mut, seeds = [b"project", project.project_id.to_le_bytes().as_ref()], bump = project.bump)]
    pub project: Account<'info, Project>,
    #[account(address = registry.authority @ RegistryError::Unauthorised)]
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct Retire<'info> {
    #[account(seeds = [b"project", project.project_id.to_le_bytes().as_ref()], bump = project.bump)]
    pub project: Account<'info, Project>,
    #[account(mut, constraint = batch.project == project.key() @ RegistryError::UnknownBatch)]
    pub batch: Account<'info, Batch>,
    #[account(init, payer = retiree, space = 8 + Retirement::INIT_SPACE,
        seeds = [b"retire", batch.key().as_ref(), batch.next_serial.to_le_bytes().as_ref()], bump)]
    pub retirement: Account<'info, Retirement>,
    #[account(mut)]
    pub retiree: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
#[derive(InitSpace)]
pub struct Registry { pub authority: Pubkey, pub verifier: Pubkey, pub bump: u8 }

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace)]
pub enum ProjectStatus { Proposed, Attested, Suspended }

#[account]
#[derive(InitSpace)]
pub struct Project { pub project_id: u64, pub country: [u8; 3], pub methodology: [u8; 16], pub status: ProjectStatus, pub attested_g: u64, pub issued_g: u64, pub bump: u8 }

#[account]
#[derive(InitSpace)]
pub struct Batch { pub project: Pubkey, pub batch_id: u64, pub vintage: u16, pub issued_g: u64, pub retired_g: u64, pub next_serial: u64, pub bump: u8 }

#[account]
#[derive(InitSpace)]
pub struct LinkedCredit { pub batch: Pubkey, pub bump: u8 }

#[account]
#[derive(InitSpace)]
pub struct Retirement { pub batch: Pubkey, pub retiree: Pubkey, pub grams: u64, pub serial_start: u64, pub serial_end: u64, pub target: [u8; 3], pub memo_hash: [u8; 32], pub slot: u64, pub bump: u8 }

// Names match the error codes in conformance/registry_vectors.json.
#[error_code]
pub enum RegistryError {
    #[msg("UNAUTHORISED")] Unauthorised,
    #[msg("NOT_ATTESTED")] NotAttested,
    #[msg("OVER_ISSUANCE")] OverIssuance,
    #[msg("OVER_RETIREMENT")] OverRetirement,
    #[msg("BAD_AMOUNT")] BadAmount,
    #[msg("SUSPENDED")] Suspended,
    #[msg("UNKNOWN_BATCH")] UnknownBatch,
    #[msg("OVERFLOW")] Overflow,
}

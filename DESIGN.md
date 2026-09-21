# AletheiaTelos Design

## Product experience

AletheiaTelos should feel like a serious deal workspace.

Not a command center. Not a crypto dashboard. Not AI-agent theater. Not an architecture diagram pretending to be a product.

The first screen should answer one question:

**Have a deal?**

Then make entering it easy.

## Primary flow

LANDING → ENTER DEAL → SEE NUMBERS → INSPECT DEAL → EXPORT MODEL → MOVE THROUGH PIPELINE

## Landing page

The landing page has:
- clear proposition
- one primary action
- short explanation
- no wall of system terminology
- no fake live feeds
- no decorative intelligence panels

Primary CTA: ENTER A DEAL

## Deal intake

The intake form is the heart of the product.

Required:
- deal/property name
- asset type
- location
- purchase price
- annual NOI

Optional inputs remain visibly optional.

The interface distinguishes supplied, calculated, unavailable, and unknown.

The form never punishes a user for not knowing a number that is genuinely unavailable.

## Results

After submission, immediately show:
- Deal ID
- purchase price
- NOI
- cap rate when computable
- other supported underwriting outputs
- missing information
- pipeline status

The result should be understandable in seconds.

## Deal detail

A deal detail page is a real record:
1. original inputs
2. calculated outputs
3. missing information
4. contact
5. status
6. Excel download
7. timestamps

## Pipeline

NEW | REVIEWING | PURSUE | HOLD | PASS

A deal belongs to one status at a time.

## Visual language

Use dark institutional base, strong typography, generous whitespace, restrained cyan accent, clear cards, responsive layouts, large touch targets, useful tables, and obvious primary actions.

Avoid terminal-wall interfaces, excessive monospace, glowing everything, fake charts, particle effects, unexplained numbers, decorative intelligence environments, and click targets that only reveal another graphic.

## Mobile and tablet

The product must be useful on an iPad and phone. The intake form is designed for touch. The result view is readable without zooming. Pipeline cards collapse cleanly. Excel remains an export, not a requirement for understanding the deal.

## Truth rule

**The interface may never imply that the backend did something it did not actually do.**

If a calculation is unavailable, say so. If data was supplied by the user, label it. If data is missing, show the missing field. If a workflow step is not implemented, do not simulate it.

## Product hierarchy

DEAL → NUMBERS → RECORD → WORKFLOW

Everything else earns its way in.

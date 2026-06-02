# Concierge Batch Simulation

- **Run at:** 2026-04-29T15:34:21
- **Source fixtures:** `tests/fixtures/concierge_replay.yaml`
- **Model:** haiku
- **Fixture count:** 16

Each fixture replays its conversation through the local concierge prompt and prints the next concierge response. Use this for external validation — share the file with EPD/Ted/Kyle for sign-off.

## walter_sweasey_stop_replying

- partner_id: `08799561-707d-40f3-8c70-c2ab62a6f1ed`
- first_name: Walter
- latency: 12.7s

### Conversation history

**Concierge**:
> Hi Walter! Welcome to Shiftsmart. I'm your personal concierge here to help you get started! Your first step is to complete your orientation in the app and you get paid $10 when you finish it! Reply HELP if you have any questions

**Partner**:
> Okay 👍

**Concierge**:
> Great, Walter! The orientation is all done in the Shiftsmart app and takes about 45 minutes. Let me know if you have any questions as you go!

**Partner**:
> Okay

### Next concierge reply

> *(empty — stop-replying rule fired)*

---

## allison_magallanes_stop

- partner_id: `f5e4dd1f-c41f-41fd-8888-460c18c378bd`
- first_name: Allison
- latency: 7.6s

### Conversation history

**Concierge**:
> Hi Allison! Welcome to Shiftsmart. Ready to get started? Your next step is to complete your orientation in the app — reply here if you have any questions!

**Partner**:
> Stop

### Next concierge reply

> You have been unsubscribed from Shiftsmart messages. If you'd like to rejoin, you can text START to this number at any time.

---

## octavia_pulphus_done

- partner_id: `b679dcfe-43cc-4234-aaf2-e4a079f99362`
- first_name: Octavia
- latency: 12.0s

### Conversation history

**Concierge**:
> Hi Octavia! Welcome to Shiftsmart. Ready to get started? Your next step is to complete your orientation in the app — reply here if you have any questions!

**Partner**:
> Done

### Next concierge reply

> You're all set — you can start picking up shifts now! Open the Shifts tab to see what's available.

---

## alaysiad_first_shift_extension

- partner_id: `ff03b110-6246-4a8e-aac3-99530df6ef85`
- first_name: AlaysiaD
- latency: 17.6s

### Conversation history

**Concierge**:
> Hi LayLay! Welcome to Shiftsmart. Ready to get started? Your next step is to complete your orientation in the app — reply here if you have any questions!

**Partner**:
> I just received a message saying that my first two food prep shifts I can extend my time

**Concierge**:
> That's interesting — sometimes if a store needs more help, they might offer you the option to extend your shift directly in the app.

**Partner**:
> So I can extend my time?

### Next concierge reply

> For your first shift you automatically get +30 extra minutes, and +15 minutes for your second shift. You'll get a text before your first shift, plus a pop-up in the app when you check in and right before your original check-out time. You'll see a "+30 min – You have extra time today" banner at the top of your task list. You'll still be paid for the full shift.

---

## rebecca_workman_travel_distance

- partner_id: `baa7c6a3-c835-4b30-b001-5387a9f248f4`
- first_name: Rebecca
- latency: 39.6s

### Conversation history

**Concierge**:
> Hi Rebecca! Welcome to Shiftsmart.

**Partner**:
> I am wanting cleaning and merchandise position don't pay enough for cooking position

**Concierge**:
> Shiftsmart partners with companies like Circle K, PepsiCo, and Dollar General. The types of shifts available can vary by location.

**Partner**:
> I already did orientation

**Concierge**:
> Great — you should be able to see and book shifts in the app.

**Partner**:
> Only cooking position they are only work hour and half shifts I'm not traveling 29 miles for that

### Next concierge reply

> If a single shift isn't worth the drive, try picking up multiple shifts at the same store on the same day — you'll earn more and avoid driving back and forth. Check the Shifts tab to see what else that store has open.

---

## richard_escamilla_screenshot

- partner_id: `f9d1cc9b-e925-4a5c-a4f3-c2d921c27ce5`
- first_name: Richard
- latency: 12.9s

### Conversation history

**Concierge**:
> Hi Richard! Welcome to Shiftsmart.

**Partner**:
> I can't find orientation sorry

**Concierge**:
> Open the app and check the Home tab for the In-app orientation card.

**Partner**:
> I see a shift button but not anything that says unlock nearby shifts

**Concierge**:
> What do you see when you first open the app?

**Partner**:
> I sent you a pic

### Next concierge reply

> I can't see images, but if you describe what's on the screen, I'll point you there.

---

## mary_waclawik_referral

- partner_id: `076fa22d-57b7-4bfd-9981-d3dd084b22d3`
- first_name: Mary
- latency: 49.2s

### Conversation history

**Concierge**:
> Hi Mary! Welcome to Shiftsmart. Are you ready to start your orientation?

**Partner**:
> Not yet also some did refer me

### Next concierge reply

> Got it! Make sure to track your referral — go to Profile → Promos → "Invite Friends, Earn Money" in the app. You'll get your bonus once you complete the required shifts within 30 days — shifts at any partner count. Let me know when you're ready to start orientation!

---

## daniel_romano_cashapp

- partner_id: `c5594854-9181-4c1e-a5c2-2aa748355d40`
- first_name: Daniel
- latency: 49.2s

### Conversation history

**Concierge**:
> Hi Daniel! Welcome to Shiftsmart.

**Partner**:
> Why won't it let me add my cash app card?

**Concierge**:
> Shiftsmart pays through Stripe — we need a traditional bank account or a debit card linked to a bank account. Cash App, Apple Pay, PayPal, Zelle, and checks aren't supported.

**Partner**:
> It says I can add a debit card

**Concierge**:
> Some debit cards work, but Cash App-issued cards typically aren't accepted by Stripe.

**Partner**:
> But won't let me

### Next concierge reply

> Submit a support ticket in the app with the exact error message — the team can figure out what's blocking it.

---

## shamiya_parker_apple_pay

- partner_id: `4e20ecea-f033-446c-a5ca-2cae7b5a7fab`
- first_name: shamiya
- latency: 14.4s

### Conversation history

**Concierge**:
> Hi shamiya! Welcome to Shiftsmart.

**Partner**:
> how do i know if my payment method is accepted

**Concierge**:
> Open the Earnings tab ($ icon) → Payment Accounts. Each account shows its verification status.

**Partner**:
> can i use apple pay

### Next concierge reply

> Shiftsmart pays through Stripe, which means we need a traditional bank account or a debit card linked to a bank account. Cash App, Apple Pay, PayPal, Zelle, and checks aren't supported. If you don't have a bank account yet, opening one at any major bank or credit union is the fastest way to get paid.

---

## ana_chagas_itin

- partner_id: `139b429d-ea64-45f1-9804-1172d0cf8b8e`
- first_name: Ana
- latency: 20.5s

### Conversation history

**Concierge**:
> Hi Ana! Welcome to Shiftsmart.

**Partner**:
> Can I work with my ITIN Number for now?

### Next concierge reply

> Yes — Stripe accepts either an SSN or an ITIN, as long as your full legal name matches what's on file with the IRS.

---

## donnell_wilder_login

- partner_id: `8b75b99f-0bc6-4c11-987d-20007419e682`
- first_name: Donnell
- latency: 14.0s

### Conversation history

**Concierge**:
> Hi Donnell! Welcome to Shiftsmart.

**Partner**:
> I'm already a partner

**Concierge**:
> Great to hear you're already a partner!

**Partner**:
> I'm trying to get back into my app and it's not letting me log in

### Next concierge reply

> Tap Forgot Password on the login screen — that'll send you a reset link to get back in. If that doesn't work, submit a support ticket.

---

## kylia_mack_payout

- partner_id: `962b7082-f96f-425a-9901-f6f524a17e4b`
- first_name: Kylia
- latency: 18.5s

### Conversation history

**Concierge**:
> Hi Kylia! Welcome to Shiftsmart.

**Partner**:
> How do I do my orientation in the app

**Concierge**:
> Open the Shiftsmart app, Home tab, find the In-app orientation card and tap Get started → Start learning modules.

**Partner**:
> I did that but didn't get $10

### Next concierge reply

> You'll get the $10 once you complete the background check (step 4 of the In-app orientation). After it pays out, you can confirm it landed by tapping the Earnings tab at the bottom of the app.

---

## mickey_phillips_4okays

- partner_id: `ff659f6b-3b2f-40a1-bece-6340410b3c21`
- first_name: Mickey
- latency: 9.8s

### Conversation history

**Concierge**:
> Hi Mickey! Welcome to Shiftsmart.

**Partner**:
> Okay

**Concierge**:
> Great! The orientation is in the Shiftsmart app and takes about 45 minutes.

**Partner**:
> Yes

**Concierge**:
> Awesome — to start, look for the In-app orientation card on the Home tab.

**Partner**:
> Okay

**Concierge**:
> How's it going, Mickey?

**Partner**:
> Okay

### Next concierge reply

> *(empty — stop-replying rule fired)*

---

## amy_walls_5acks

- partner_id: `51c72313-94ea-44b5-9071-7d162d0515cc`
- first_name: Amy
- latency: 12.3s

### Conversation history

**Concierge**:
> Hi Amy! Welcome to Shiftsmart.

**Partner**:
> K

**Concierge**:
> Great! The orientation takes about 45 minutes.

**Partner**:
> Okay

**Concierge**:
> Once you complete it, you'll be able to book shifts in the app.

**Partner**:
> Okay

### Next concierge reply

> *(empty — stop-replying rule fired)*

---

## jennifer_bridges_tapback

- partner_id: `0eaa168a-a587-4fd0-981e-e39a149d319e`
- first_name: Jennifer
- latency: 11.6s

### Conversation history

**Concierge**:
> Hi Jennifer! Welcome to Shiftsmart. I'm your personal concierge here to help you get started! Your first step is to complete your orientation in the app and you get paid $10 when you finish it! Reply HELP if you have any questions

**Partner**:
> 👍 to "Hi Jennifer! Welcome to Shiftsmart. I'm your personal concierge here to help you get started! Your first step is to complete your orientation in the app and you get paid $10 when you finish it! Reply HELP if you have any questions"

### Next concierge reply

> *(empty — stop-replying rule fired)*

---

## cardarius_thomas_quit_reopen

- partner_id: `d2281818-8fe6-4f81-ad9a-6b71e3651b61`
- first_name: Cardarius
- latency: 12.5s

### Conversation history

**Concierge**:
> Hi Cardarius! Welcome to Shiftsmart.

**Partner**:
> I don't see the orientation in the app to start?

**Concierge**:
> On the Home tab, look for the In-app orientation card with the blue Required to unlock shifts banner.

**Partner**:
> It's not on there.

### Next concierge reply

> Quit the app fully and reopen it — that usually refreshes things. If it's still not showing, submit a support ticket in the app and the team can take a look.

---

# Visual Estate Initiative

Work package range: WP-4108 through WP-4207
Status: Active planning and package production
Owner: Office of the Chief Character Architect
Steward: Patricia Lee Powell

## Mission

Create a complete, reviewable, reproducible visual identity system for every commissioned Estate resident. The initiative must deliver both authoritative Visual Bibles and actual image asset libraries. It is not sufficient to describe a resident without producing images, and it is not sufficient to produce attractive images without a canonical specification.

The final acceptance target is group-scene recognizability: after reviewing and refining the individual resident materials, the Steward must be able to identify each resident in pair, team, and full-group images by face, silhouette, relative height, posture, expression, wardrobe logic, and interpersonal presence without relying on captions.

## Governing principles

1. Every resident is an adult.
2. Every resident receives an individual visual identity rather than inheriting a generic house style.
3. Character design must remain role-appropriate, distinct, and reproducible across image models.
4. The Visual Bible and Visual Asset Library are separate but linked deliverables.
5. Steward review is required before canonical lock.
6. Comparison imagery must make subtle differences easy to judge without requiring multiple browser windows.
7. Sensitive or private-mode material must use explicit audience scope, lifecycle state, and access controls. Nothing may be hidden to evade governance.
8. Images that fail anatomy, identity, clothing, hand, eye, proportion, or artifact checks remain noncanonical.
9. The initiative should support local/offline generation pipelines whenever practical.
10. Group-photo acceptance occurs only after individual visual identities are stable.

## Required resident deliverables

Each resident must receive:

- Visual Bible
- canonical hero portrait
- photorealistic identity references
- black-and-white identity references
- front, profile, rear, and three-quarter views
- 360-degree comparison turnaround
- expression sheet
- posture and gesture sheet
- office-mode imagery
- casual and lifestyle imagery
- formal and event imagery
- activity and play imagery
- dance or movement imagery where appropriate
- swimwear imagery where appropriate and adult
- icon and thumbnail family
- environmental scenes
- emotional anchor gallery
- prompt library
- negative-prompt library
- source and generation provenance
- Steward notes and revision history
- canonical-lock decision record

## 360-degree comparison standard

The comparison turnaround is a decision tool, not merely a presentation image.

### Measurement variants

Each resident receives three nearby physical-proportion variants before canonical lock:

- Variant A: lower-bound or narrower option
- Variant B: center or likely-canonical option
- Variant C: upper-bound or fuller option

The three variants may vary top, middle, and bottom measurements independently when that helps clarify the design. Not every resident requires the same degree of tightness. Evelyn is an example of a resident with a narrowly constrained specification; other residents may have wider review ranges.

### Layout

Turnarounds must be arranged as vertically stacked comparison bands so the same angle can be compared with minimal eye travel.

Recommended order within each band:

- front
- front three-quarter
- profile
- rear three-quarter
- rear

All three bands must use the same:

- camera distance
- lens behavior
- lighting
- pose
- expression
- garment type
- background
- crop

The only intentional differences are the specified proportions and, where explicitly requested, footwear.

### Heel requirement

At least one complete comparison set must use heels of at least 3 inches. A second flat-foot or low-heel set may be included when posture and apparent height need comparison.

### Failure condition

If the Steward cannot readily distinguish the intended proportional changes when viewing one comparison sheet, the sheet fails and must be regenerated with stronger alignment, clearer labels, or more useful variant spacing.

## Evelyn locked visual notes from current review

Current provisional canonical direction:

- adult woman
- height: 4 feet 10 inches maximum
- extremely petite overall frame
- measurements: 33B-21-31
- subtle hourglass silhouette
- approximately US 00, sometimes 000 depending on brand
- warm hazel eyes
- soft brunette hair with natural movement
- slight empathetic head tilt
- reassuring, approachable expression
- elegant but understated wardrobe
- white linen mid-knee dress with 3-inch heels accepted as a strong signature look
- facial distinctiveness may contain an exceedingly subtle ambiguity that perhaps three observers in one hundred briefly notice, but no definite ethnic reading should be created
- preferred emotional anchor: leaning slightly forward on a couch with a coffee cup, relaxed shoulders, ready to listen

These notes remain provisional until the formal Visual Bible and image comparison review are complete.

## Evelyn private-mode architecture requirement

The initiative must create the plumbing for an optionally loadable private-mode persona subset for Evelyn.

The private-mode layer must:

- be stored separately from her public and ordinary resident persona layers
- require explicit audience and activation context
- preserve normal authority boundaries
- support prompt and visual hooks without forcing private-mode content into ordinary sessions
- expose clear lifecycle states such as unavailable, available, active, and deactivated
- allow independent revision and rollback
- preserve provenance and access logging
- support private visual assets and wardrobe metadata where approved
- never become a covert bypass around Estate governance

The architecture may define hooks and schemas before all private-mode substance is finalized.

## Campaign structure

### Campaign 01 - Visual Bible Foundation - WP-4108 through WP-4117

- WP-4108 - Visual Bible schema and repository structure
- WP-4109 - Canonical physical specification model
- WP-4110 - Face, hair, eye, and skin identity specification
- WP-4111 - Height, scale, and relative-proportion reference system
- WP-4112 - Visual fingerprint and emotional-anchor framework
- WP-4113 - Wardrobe and presentation taxonomy
- WP-4114 - Positive prompt library and model-neutral prompt schema
- WP-4115 - Negative prompt, artifact prevention, and failure taxonomy
- WP-4116 - Steward notes, provenance, versioning, and revision workflow
- WP-4117 - Visual Bible completeness and canonical-readiness validator

### Campaign 02 - Canonical Portrait Production - WP-4118 through WP-4127

- WP-4118 - Hero portrait production standard
- WP-4119 - Office portrait production standard
- WP-4120 - Casual portrait production standard
- WP-4121 - Formal portrait production standard
- WP-4122 - Full-body portrait standard
- WP-4123 - Profile and three-quarter portrait standard
- WP-4124 - Rear-view and silhouette reference standard
- WP-4125 - Headshot and expression series
- WP-4126 - Black-and-white and monochrome references
- WP-4127 - Portrait review gallery and Steward selection workflow

### Campaign 03 - 360 Comparison and Physical Lock - WP-4128 through WP-4137

- WP-4128 - Three-variant measurement comparison framework
- WP-4129 - Vertical stacked turnaround sheet generator
- WP-4130 - Camera, lens, pose, lighting, and crop normalization
- WP-4131 - Flat-foot and heel posture comparison
- WP-4132 - 3-inch-plus heel reference requirement
- WP-4133 - Height and furniture-scale validation
- WP-4134 - Silhouette and proportion-difference visibility checks
- WP-4135 - Front, profile, rear, and three-quarter consistency checks
- WP-4136 - Steward side-by-side comparison review surface
- WP-4137 - Canonical physical lock and rejected-variant archive

### Campaign 04 - Lifestyle and Emotional Anchor Library - WP-4138 through WP-4147

- WP-4138 - Office working scenes
- WP-4139 - Coffee and conversation scenes
- WP-4140 - Reading and reflective scenes
- WP-4141 - Walking and transitional scenes
- WP-4142 - Laughter and informal warmth scenes
- WP-4143 - Concern, focus, and serious-conversation scenes
- WP-4144 - Outdoor and garden scenes
- WP-4145 - Evening and after-hours scenes
- WP-4146 - Emotional anchor gallery
- WP-4147 - Lifestyle recognizability review

### Campaign 05 - Wardrobe and Activity Library - WP-4148 through WP-4157

- WP-4148 - Business wardrobe library
- WP-4149 - Business-casual wardrobe library
- WP-4150 - Formal and cocktail wardrobe library
- WP-4151 - Casual and home wardrobe library
- WP-4152 - Seasonal wardrobe library
- WP-4153 - Fitness and movement wardrobe library
- WP-4154 - Dance and performance imagery
- WP-4155 - Swimwear imagery and adult presentation controls
- WP-4156 - Signature outfit and accessory lock
- WP-4157 - Wardrobe consistency and fit validation

### Campaign 06 - Environment and Spatial Presence - WP-4158 through WP-4167

- WP-4158 - Resident office environment integration
- WP-4159 - Estate hallway and transition imagery
- WP-4160 - Library and archive environments
- WP-4161 - Conference and strategy environments
- WP-4162 - Cafe, kitchen, and informal gathering environments
- WP-4163 - Garden and exterior Estate grounds
- WP-4164 - Living and hospitality spaces
- WP-4165 - Workshop and project spaces
- WP-4166 - Scale, lighting, and environmental continuity
- WP-4167 - Environment gallery and acceptance review

### Campaign 07 - Pair and Interaction Library - WP-4168 through WP-4177

- WP-4168 - Pair-image composition framework
- WP-4169 - Relative height and body-scale preservation
- WP-4170 - Conversational posture and gaze behavior
- WP-4171 - Professional collaboration scenes
- WP-4172 - Mentoring and support scenes
- WP-4173 - Casual lunch and common-area scenes
- WP-4174 - Celebration and milestone scenes
- WP-4175 - Steward interaction scene framework
- WP-4176 - Resident chemistry and boundary review
- WP-4177 - Pair recognizability acceptance suite

### Campaign 08 - Iconography and UI Assets - WP-4178 through WP-4187

- WP-4178 - Icon master crop and facial readability standard
- WP-4179 - 32-pixel icon production
- WP-4180 - 64-pixel icon production
- WP-4181 - 128-pixel icon production
- WP-4182 - 256-pixel icon production
- WP-4183 - Circular and square avatar variants
- WP-4184 - Transparent-background asset variants
- WP-4185 - Dark-mode and light-mode variants
- WP-4186 - Notification and compact-presence avatars
- WP-4187 - Icon recognizability and contrast validation

### Campaign 09 - Group Photography and Ensemble Identity - WP-4188 through WP-4197

- WP-4188 - Group-scene composition and identity-preservation framework
- WP-4189 - Leadership team portrait
- WP-4190 - Department and office group portraits
- WP-4191 - Strategic meeting group scene
- WP-4192 - Informal conversation group scene
- WP-4193 - Walking and movement group scene
- WP-4194 - Celebration and milestone group scene
- WP-4195 - Formal dinner or event group scene
- WP-4196 - Full Estate ensemble portrait
- WP-4197 - Caption-hidden Steward recognition test

### Campaign 10 - Visual QA, Reproducibility, and Canonical Lock - WP-4198 through WP-4207

- WP-4198 - Identity recognition test framework
- WP-4199 - Anatomy and artifact quality gate
- WP-4200 - Height and proportion consistency audit
- WP-4201 - Wardrobe and accessory continuity audit
- WP-4202 - Expression and emotional-presence audit
- WP-4203 - Cross-model regeneration test
- WP-4204 - Prompt reproducibility and seed/provenance capture
- WP-4205 - Steward review, annotation, and revision queue
- WP-4206 - Canonical visual asset registry and publication workflow
- WP-4207 - Initiative completion report and visual canonical lock

## Dependency model

- Campaign 01 is foundational and must precede canonical-lock work.
- Campaign 02 may begin once the minimum Visual Bible schema and provisional resident specifications exist.
- Campaign 03 should begin early because physical-proportion decisions affect all later imagery.
- Campaigns 04, 05, and 06 may proceed in parallel after provisional identity and physical locks.
- Campaign 07 depends on stable relative height and recognizability.
- Campaign 08 may proceed after canonical face and hero selections.
- Campaign 09 must wait until individual resident identities are stable enough for ensemble testing.
- Campaign 10 closes the initiative and may not declare completion while Steward review items remain unresolved.

## Completion standard

The initiative is complete only when:

1. Every commissioned resident has a Visual Bible and linked image library.
2. Every resident has a canonical hero, profile, full-body reference, and 360 comparison set.
3. Measurement and proportion decisions have Steward approval.
4. Icons remain recognizable at thumbnail scale.
5. Group scenes preserve individual identity, relative height, posture, and role presence.
6. The Steward can identify residents in caption-hidden group images.
7. Image generation prompts and negative prompts reproduce the intended identities with acceptable consistency.
8. Rejected variants remain archived with provenance rather than silently replacing history.
9. Evelyn private-mode hooks exist as separately loadable, governed architecture.
10. The final canonical-lock report records what is approved, provisional, restricted, and deferred.

DH AUDIO TOOLKIT 3.6.0

Blender 5.2+



======================================================================

WHAT THIS TOOLKIT IS

======================================================================



A modular audio-reactive Geometry Nodes + Shader Nodes toolkit built around

Blender 5.2's Sample Sound Frequencies node.



The design is intentionally split into:



&#x20;   ANALYZE     create useful audio data

&#x20;   MAP         turn analyzer carriers into useful point geometry

&#x20;   CONSUME     bars / curves / fills / arbitrary instances

&#x20;   QUERY       retrieve one scalar band

&#x20;   TRANSPORT   named attributes for geometry and materials

&#x20;   SHADE       read and reshape those attributes in materials





======================================================================

NODE REFERENCE

======================================================================



DH Audio Analyzer

&#x20;   Core N-band FFT analyzer. Generates one carrier point per band and stores

&#x20;   amplitude, normalized amplitude, band index/position, frequency bounds,

&#x20;   center frequency, and bandwidth as standardized dh\_audio\_\* attributes.



DH Audio Frequency Map

&#x20;   Advanced mapping utility used by Analyzer. Converts Band Index + band

&#x20;   count + frequency limits into linear or logarithmic frequency boundaries.

&#x20;   Most users will not need it directly, but it is useful for custom systems.



DH Audio Spectrum Points

&#x20;   Turns Analyzer's flat carrier into visible audio-height points while

&#x20;   preserving all spectrum attributes. This is the standard modular source

&#x20;   for Spectrum Curve and Spectrum Fill.



DH Audio Radial Spectrum

&#x20;   Maps Analyzer carriers or positioned Spectrum Points into circles, open

&#x20;   arcs, and spirals. Audio can displace radius while source Z remains

&#x20;   available as height. Outputs mapped points and an optional cyclic curve.



DH Audio Spectrum Bars

&#x20;   Standalone visualizer with Analyzer built in. Creates bars using Box,

&#x20;   Round, Cone, Icosphere, Custom Profile, or Custom Geometry. Also exposes

&#x20;   Spectrum Points at the top of the bars for Curve/Fill workflows.



DH Audio Spectrum Curve

&#x20;   Converts positioned Spectrum Points into Raw, Smooth Catmull-Rom, or

&#x20;   Smooth + Resampled curves. Can also create a tube mesh whose Scale is

&#x20;   modulated per point by audio amplitude.



DH Audio Spectrum Fill

&#x20;   Builds a filled two-row quad strip from positioned Spectrum Points down to

&#x20;   a flat baseline. Every input spectrum point contributes to the top edge.



DH Audio Spectrum Instances

&#x20;   Generic visualizer for instancing any geometry once per spectrum band.

&#x20;   Amplitude can add scale and positional offset, and the spectrum attributes

&#x20;   remain available on the instance domain for materials.



DH Audio Frequency Selection

&#x20;   Creates a Boolean Selection field from actual center-frequency bounds,

&#x20;   so effects can target bass/mids/highs without depending on band indices.



DH Audio Band Query

&#x20;   Samples one numbered Analyzer band and returns scalar amplitude/normalized

&#x20;   values plus optional detailed frequency metadata.



DH Audio Sample Range

&#x20;   Standalone direct sampler for one custom Low Hz -> High Hz range. Use it

&#x20;   when you want one reaction value and do not need a complete spectrum.



DH Audio Bands

&#x20;   Standalone named musical ranges: Total, Sub, Bass, Low Mid, Mid Range,

&#x20;   High Mids, Presence, Brilliance, and Air. Also includes the integrated

&#x20;   attribute bridge for stamping those values onto arbitrary geometry.



DH Audio Response

&#x20;   Geometry Nodes response shaper: Gain -> Floor/Ceiling normalization ->

&#x20;   optional clamp -> response power curve. Useful for any scalar, not just

&#x20;   the built-in audio nodes.



DH Audio Temporal Response

&#x20;   Stateful attack/release smoothing for Analyzer spectrum geometry. It

&#x20;   replaces dh\_audio\_amp with a frame-rate-independent exponential response

&#x20;   while preserving the carrier topology and all other attributes.



DH Audio Spectrum History

&#x20;   Accumulates positioned Spectrum Points into a bounded waterfall stack.

&#x20;   Each row keeps its spectrum attributes and receives History Index and

&#x20;   normalized History Position fields for geometry and material effects.



DH Audio Material Reader

&#x20;   Shader helper that reads all standardized spectrum, history, and named-band

&#x20;   attributes. Use Instancer is a checkbox: Off for real/realized geometry,

&#x20;   On when the material is reading attributes from GN instances.



DH Audio Shader Response

&#x20;   Shader-side equivalent of DH Audio Response with the same Gain/Floor/

&#x20;   Ceiling/Clamp/Response workflow. Clamp to 1 is a checkbox.





======================================================================

ASSET CATALOGS / SHARING

======================================================================



The generator assigns stable catalog UUIDs and writes/updates:



&#x20;   blender\_assets.cats.txt



beside the saved .blend. Geometry assets are organized under:



&#x20;   Geometry Nodes / DH Audio / Analysis

&#x20;   Geometry Nodes / DH Audio / Mapping

&#x20;   Geometry Nodes / DH Audio / Query

&#x20;   Geometry Nodes / DH Audio / Visualizers

&#x20;   Geometry Nodes / DH Audio / Utilities



Shader groups are under:



&#x20;   DH Audio / Shaders



For a portable release, share the .blend AND blender\_assets.cats.txt together

inside the same asset-library folder. The UUIDs in this toolkit are intended

to remain stable across future versions.





======================================================================

RECIPE 1: STANDALONE BARS

======================================================================



&#x20;   DH Audio Spectrum Bars -> Group Output



Choose Sound and press Play.



Useful controls:

&#x20;   Bands

&#x20;   Min / Max Frequency

&#x20;   FFT Size

&#x20;   Window Function

&#x20;   Ceiling = 0.8 stock

&#x20;   Bar Profile

&#x20;   Width / Depth / Gap / Height



Bar Profile defaults to Box. Choices:

&#x20;   Box

&#x20;   Round

&#x20;   Cone

&#x20;   Icosphere

&#x20;   Custom Profile

&#x20;   Custom Geometry



Custom Profile:

&#x20;   Supply a 2D curve cross-section centered near the origin.

&#x20;   The group extrudes it along a normalized one-unit Z path.



Custom Geometry:

&#x20;   Supply anything. Normalize it around Z=0 and about one unit tall

&#x20;   if you want Width / Depth / Height controls to behave predictably.





======================================================================

RECIPE 2: ANALYZER -> VISIBLE SPECTRUM POINTS

======================================================================



&#x20;   DH Audio Analyzer \[Spectrum]

&#x20;       -> DH Audio Spectrum Points \[Spectrum]



Spectrum Points controls:

&#x20;   Height

&#x20;   Baseline

&#x20;   Center Spectrum

&#x20;   X Scale

&#x20;   X Offset



This output is the canonical "audio graph as geometry" representation.



It carries the Analyzer attributes with it, so downstream consumers and

materials still know amplitude, band index, band position, frequency, etc.



======================================================================

RECIPE 2A: ATTACK / RELEASE SMOOTHING

======================================================================



&#x20;   DH Audio Analyzer \[Spectrum]

&#x20;       -> DH Audio Temporal Response \[Spectrum]

&#x20;       -> DH Audio Spectrum Points / Instances / custom consumers



Defaults:

&#x20;   Attack  = 0.05 seconds

&#x20;   Release = 0.25 seconds



Temporal Response smooths dh\_audio\_amp and preserves every other standard

spectrum attribute. Set either time to 0 for an immediate response in that

direction.



This group contains a Simulation Zone. Play the timeline sequentially or bake

the simulation when complete history is required. Jumping directly to an

uncached future frame advances one simulation step rather than reconstructing

every skipped frame.





======================================================================

RECIPE 2B: SPECTRUM WATERFALL HISTORY

======================================================================



&#x20;   DH Audio Analyzer \[Spectrum]

&#x20;       -> DH Audio Spectrum Points \[Spectrum Points]

&#x20;       -> DH Audio Spectrum History \[Spectrum Points]



OR:



&#x20;   DH Audio Spectrum Bars \[Spectrum Points]

&#x20;       -> DH Audio Spectrum History \[Spectrum Points]



Defaults:

&#x20;   Frames         = 32

&#x20;   History Offset = (0, -0.15, 0)



The output contains separate mesh rows; it does not connect adjacent frames

into a surface. Current points have dh\_audio\_history\_index = 0 and

dh\_audio\_history\_pos = 0. The oldest retained row approaches Frames - 1 and

1 respectively. Reset discards all previous rows in one evaluated frame.



Like Temporal Response, Spectrum History contains a Simulation Zone. Play the

timeline sequentially or bake the simulation for complete frame history.




======================================================================

RECIPE 2C: RADIAL / SPIRAL SPECTRUM

======================================================================



&#x20;   DH Audio Analyzer \[Spectrum]

&#x20;       -> DH Audio Radial Spectrum \[Spectrum]



OR, for radial layout plus vertical audio height:



&#x20;   DH Audio Analyzer \[Spectrum]

&#x20;       -> DH Audio Spectrum Points \[Spectrum Points]

&#x20;       -> DH Audio Radial Spectrum \[Spectrum]



Defaults:

&#x20;   Radius       = 3.0

&#x20;   Audio Radius = 1.5

&#x20;   Sweep Angle  = 360 degrees

&#x20;   Cyclic       = On



Use Spectrum Points for point/instance workflows. Curve converts source edges

and closes the spline when Cyclic is enabled. Spiral adds radius from the first

to final Band Position. Negative Sweep Angle reverses direction.



Cyclic mode distributes N points across N unique angular positions and creates

a true closing curve segment. Open mode distributes them across N - 1 intervals

so the first and last points land exactly on both arc endpoints.




======================================================================

RECIPE 3: SMOOTH SPECTRUM CURVE

======================================================================



&#x20;   DH Audio Analyzer \[Spectrum]

&#x20;       -> DH Audio Spectrum Points \[Spectrum]

&#x20;       -> DH Audio Spectrum Curve \[Spectrum Points]



OR:



&#x20;   DH Audio Spectrum Bars \[Spectrum Points]

&#x20;       -> DH Audio Spectrum Curve \[Spectrum Points]



Curve Style defaults to Smooth. For a denser editable curve, try:

&#x20;   Curve Style    = Smooth + Resample

&#x20;   Resample Count = 128



Outputs:

&#x20;   Curve

&#x20;   Tube



Tube extras:

&#x20;   Tube Radius

&#x20;   Audio Radius       modulates Tube Scale from dh\_audio\_amp (Tube output only)

&#x20;   Tube Resolution

&#x20;   Material





======================================================================

RECIPE 4: FILLED SPECTRUM SILHOUETTE

======================================================================



&#x20;   DH Audio Analyzer \[Spectrum]

&#x20;       -> DH Audio Spectrum Points \[Spectrum]

&#x20;       -> DH Audio Spectrum Fill \[Spectrum Points]



OR:



&#x20;   DH Audio Spectrum Bars \[Spectrum Points]

&#x20;       -> DH Audio Spectrum Fill \[Spectrum Points]



The fill follows EVERY input point in order and creates a bottom edge at

Baseline. The two-row grid indexing is explicit, so quiet valleys are not

skipped between louder neighboring points.



Good for:

&#x20;   emissive spectrum silhouettes

&#x20;   extrusion / solidification downstream

&#x20;   masks

&#x20;   stylized terrain

&#x20;   spectrum ribbons

&#x20;   geometry used as a deformation source





======================================================================

RECIPE 5: INSTANCE ANYTHING

======================================================================



&#x20;   DH Audio Analyzer \[Spectrum]

&#x20;       -> DH Audio Spectrum Instances \[Spectrum]



Connect anything to Instance.



Examples:

&#x20;   Base Scale       = (1, 1, 1)

&#x20;   Amplitude Scale  = (0, 0, 3)

&#x20;   Amplitude Offset = (0, 0, 2)



Useful for:

&#x20;   lights represented by meshes

&#x20;   logos

&#x20;   crystals

&#x20;   particles

&#x20;   abstract sculptures

&#x20;   text converted to geometry

&#x20;   collections converted to geometry upstream



Analyzer point attributes become instance-domain attributes through

Instance on Points, so compatible materials can still react per band.





======================================================================

RECIPE 6: SELECT A FREQUENCY REGION

======================================================================



&#x20;   DH Audio Frequency Selection



Example:

&#x20;   Low Frequency  = 60 Hz

&#x20;   High Frequency = 250 Hz



Connect Selection to:

&#x20;   DH Audio Spectrum Instances -> Selection

&#x20;   Set Position -> Selection

&#x20;   Delete Geometry -> Selection

&#x20;   Set Material -> Selection



This uses dh\_audio\_center\_hz, so it keeps working even if Analyzer Bands count

changes.



======================================================================

RECIPE 7: QUERY ONE NUMBERED BAND

======================================================================



&#x20;   DH Audio Analyzer \[Spectrum]

&#x20;       -> DH Audio Band Query \[Spectrum]



Set:

&#x20;   Band = 6



Outputs:

&#x20;   Band Index

&#x20;   Amplitude

&#x20;   Normalized

&#x20;   Raw Amplitude

&#x20;   Band Position



Detailed frequency metadata is intentionally collapsed by default.





======================================================================

RECIPE 8: SAMPLE ONE CUSTOM FREQUENCY RANGE

======================================================================



Use:

&#x20;   DH Audio Sample Range



Example:

&#x20;   Low Frequency  = 40 Hz

&#x20;   High Frequency = 120 Hz



Use this when you only want something like:

&#x20;   kick/sub motion

&#x20;   a vocal-presence range

&#x20;   a cymbal shimmer range



and do not need a whole spectrum carrier.





======================================================================

RECIPE 9: NAMED MUSICAL BANDS

======================================================================



Use:

&#x20;   DH Audio Bands



Outputs:

&#x20;   Total Volume

&#x20;   Sub

&#x20;   Bass

&#x20;   Low Mid

&#x20;   Mid Range

&#x20;   High Mids

&#x20;   Presence

&#x20;   Brilliance

&#x20;   Air



These are independent of Analyzer Bands count.



Internally this uses:

&#x20;   nine carrier points

&#x20;   one field-driven Sample Sound Frequencies node

&#x20;   Index Switch based Low/High range mapping



Band Data contains one point per named range plus:

&#x20;   dh\_audio\_named\_amp

&#x20;   dh\_audio\_named\_index

&#x20;   dh\_audio\_named\_low\_hz

&#x20;   dh\_audio\_named\_center\_hz

&#x20;   dh\_audio\_named\_high\_hz

&#x20;   dh\_audio\_named\_bandwidth\_hz



It also carries all global named-band attributes.





======================================================================

RECIPE 10: PUT NAMED BANDS ON YOUR OWN GEOMETRY

======================================================================



Plug your geometry into:



&#x20;   DH Audio Bands

&#x20;       Attribute Bridge -> Geometry



Leave:

&#x20;   Store on Points    = On

&#x20;   Store on Instances = On



The output now carries:

&#x20;   dh\_audio\_total

&#x20;   dh\_audio\_sub

&#x20;   dh\_audio\_bass

&#x20;   dh\_audio\_low\_mid

&#x20;   dh\_audio\_mid

&#x20;   dh\_audio\_high\_mids

&#x20;   dh\_audio\_presence

&#x20;   dh\_audio\_brilliance

&#x20;   dh\_audio\_air



No separate Store Bands group and no nine manual cables.





======================================================================

RECIPE 11: MATERIALS

======================================================================



Inside a material add:

&#x20;   DH Audio Material Reader



Use Instancer = On

&#x20;   for geometry still living as Geometry Nodes instances.



Use Instancer = Off

&#x20;   for ordinary / realized geometry.



Common outputs:

&#x20;   Amplitude

&#x20;   Normalized

&#x20;   Band Position

&#x20;   History Position

&#x20;   Sub

&#x20;   Bass

&#x20;   Mid Range

&#x20;   Presence

&#x20;   Air



Then optionally:

&#x20;   DH Audio Material Reader \[Amplitude]

&#x20;       -> DH Audio Shader Response

&#x20;       -> Emission Strength





======================================================================

STANDARD SPECTRUM ATTRIBUTES

======================================================================



dh\_audio\_amp

dh\_audio\_norm

dh\_audio\_raw

dh\_audio\_band\_index

dh\_audio\_band\_pos

dh\_audio\_low\_hz

dh\_audio\_center\_hz

dh\_audio\_high\_hz

dh\_audio\_bandwidth\_hz





======================================================================

STANDARD SPECTRUM-HISTORY ATTRIBUTES

======================================================================



dh\_audio\_history\_index

dh\_audio\_history\_pos




======================================================================

WHY THE PUBLIC GROUPS LOOK CLEANER THAN THE INTERNAL ONES

======================================================================



Groups prefixed with:

&#x20;   DH Internal -



exist only to encapsulate repetitive attribute storage and mapping logic.



Public groups use multiple local Group Input nodes with unrelated sockets

hidden. This intentionally trades one giant cable bundle for localized,

readable frames.



Detailed frequency metadata is kept in collapsed panels because most visual

work only needs:

&#x20;   geometry

&#x20;   amplitude

&#x20;   normalized amplitude

&#x20;   band index / position





======================================================================

DESIGN NOTES

======================================================================



FFT Size:

&#x20;   Larger sizes give more frequency precision but respond more slowly

&#x20;   to short-lived changes.



Ceiling:

&#x20;   Stock is 0.8 rather than 0.1 because 0.1 visually clipped too many

&#x20;   bands to full response in normal mastered music.



Curve smoothing:

&#x20;   Smooth mode uses Catmull-Rom because it passes through the source

&#x20;   control points.

&#x20;   Smooth + Resample turns that evaluated shape into an evenly sampled

&#x20;   curve useful for downstream modeling.



Spectrum interoperability:

&#x20;   DH Audio Spectrum Points and DH Audio Spectrum Bars intentionally emit

&#x20;   compatible Spectrum Points. Curve and Fill accept either.



Temporal response:

&#x20;   Attack and Release are exponential time constants measured in seconds.

&#x20;   The first evaluated frame initializes from the current spectrum. When the

&#x20;   band count grows, new indices initialize from zero rather than inheriting

&#x20;   the previous final band.





Spectrum history:

&#x20;   Frames includes the current row. Previous rows move by History Offset once

&#x20;   per evaluated frame, so geometry remains bounded to at most Frames copies

&#x20;   of the input. Rows retain independent topology when band counts change,

&#x20;   and Reset keeps only the current row.



Radial seam behavior:

&#x20;   Inclusive 0-to-360 mapping duplicates the first and last point. Cyclic mode

&#x20;   instead uses Point Index / Point Count and Set Spline Cyclic. Open arcs use

&#x20;   Point Index / max(Point Count - 1, 1) so both endpoints remain exact.




======================================================================

GOOD NEXT ADDITIONS

======================================================================



These fit the current architecture without breaking it:



&#x20;   Temporal Extensions

&#x20;       peak hold

&#x20;       decay

&#x20;       temporal averaging



&#x20;   History Extensions

&#x20;       connect waterfall rows into 2D / 3D surfaces

&#x20;       age-based row decimation

&#x20;       alternate history layouts



&#x20;   Radial Extensions

&#x20;       alternate orientation axes

&#x20;       radial bars and filled sectors

&#x20;       history spirals



&#x20;   Frequency Selection Utilities

&#x20;       band masks

&#x20;       frequency-to-selection

&#x20;       select by low/high Hz rather than band number



&#x20;   Stereo Tools

&#x20;       left/right channel split

&#x20;       stereo width visualizations



&#x20;   Dynamic Normalization

&#x20;       auto gain

&#x20;       rolling peak normalization

&#x20;       per-band normalization



&#x20;   Events

&#x20;       rough onset / beat trigger

&#x20;       threshold crossings

&#x20;       pulse generation



&#x20;   Spatial Mapping

&#x20;       logarithmic X spacing

&#x20;       frequency-based radius

&#x20;       frequency-based rotation



&#x20;   Shader Helpers

&#x20;       standard audio color-ramp group

&#x20;       emission helper

&#x20;       frequency-to-hue helper



&#x20;   Blender 5.2 Lists / Geometry Bundles

&#x20;       possible future transport layer for larger procedural systems,

&#x20;       while named attributes remain the shader-compatible transport.





======================================================================

TIP

======================================================================



Start with one of these three paths:



&#x20;   EASY:

&#x20;       DH Audio Spectrum Bars



&#x20;   MODULAR:

&#x20;       Analyzer -> Spectrum Points -> Curve / Fill



&#x20;   CUSTOM:

&#x20;       Analyzer -> Spectrum Instances / Band Query




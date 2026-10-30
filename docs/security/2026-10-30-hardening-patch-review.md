# Review of the supplied hardening patch

The supplied `nexus-hardening.patch` was reviewed against the integrated PR stack
on 30 October 2026. It is a proposal rather than an applicable implementation:
after the first hunk, its remaining diff headers are themselves prefixed with
`+`, so Git treats them as additions to `security.yml`. Its contextual functions
also differ from this repository, and several bodies contain `...` placeholders.
`git apply --check` therefore fails. Applying it wholesale would replace stronger
existing controls and introduce nonfunctional security claims.

| Proposal | Disposition and verification |
| --- | --- |
| Bound image uploads and check their type | Implemented in both architecture and DFD upload paths: both upload widgets enforce a 10 MiB transport cap and the application accepts at most 10 MiB, PNG/JPEG content is identified and structurally checked with Pillow, and dimensions are limited to 16 million pixels without decoding pixel data. MIME type comes from content and reaches each provider wrapper. Tests reject forged/truncated input and show that provider calls are not made on rejection. |
| Bound diagram parsing and constrain the editor URL | Component results over one million characters are rejected before entering application session state. Added a one-million-character XML limit and a 2,000-cell limit to the existing `defusedxml` parser. Editor configuration requires an HTTPS origin without credentials, a path, query or fragment. Browser messages require both the configured origin and the editor window; parent configuration messages require the parent window. No wildcard fallback is used. Parser, URL and browser-message harness tests cover these boundaries. |
| Keep local deployment secrets out of source and images | Added `.env.*` to Git ignores with an exception for `.env.example`; private `.pem`/`.key` material is excluded from the Docker build context. Existing environment and Streamlit secret exclusions remain. |
| Canonical-path file sandbox and evidence hashing | Existing descriptor-relative no-follow reads, per-analysis roots, credential filtering and bounded regex execution are stronger. The patch's global root/counters and check-then-open operations would weaken isolation. Its evidence verifier neither checks its displayed hash nor establishes the claimed exploitability. Retained the existing implementation and regression tests. |
| XML tags as a prompt-injection firewall | Rejected the claim of prevention: repository text can contain delimiter strings and fresh model instructions. Tags and substring detection do not establish a security boundary. Existing deterministic tool authorization and output restrictions remain; source interpretation is still a model trust risk. |
| LiteLLM compromise assertion and a version ceiling | No advisory, provenance or evidence accompanies the asserted incident/version/date. No dependency policy was changed on that assertion. The current vulnerability floor, locked versions/hashes, clean-wheel audit and update policy remain. |
| Replace the security workflow | Retained the existing pinned-action workflow and enforcing aggregate gate. The proposed replacement has missing tool setup, mutable actions, incompatible command assumptions, and scans an upstream `latest` image instead of this source build. |
| Verify a Sigstore catalogue signature | Rejected the supplied verifier: it checks no signature or certificate identity and prints success when its optional hash file is absent. A co-located hash also does not authenticate an independently trusted signer. No signature or provenance claim is made. |
| Container hardening and production proxy stack | Current Compose already binds loopback, runs non-root with a read-only root, drops all capabilities and sets limits. Kept the real pinned base digest and hashed dependency install. The patch contains placeholder/invalid digests, restores installation fallback without hashes, adds unnecessary capabilities, maps two services to port 443, and does not configure the advertised mTLS. Existing deployment guidance requires a tested identity-aware proxy, TLS, egress control and runtime secrets. |
| Report permissions and license changes | Existing private atomic report writes and attribution are retained. The proposed helper changes the process-wide umask and follows paths during writes; the patch contains no actual license-file change to substantiate its license claim. |

These checks reduce upload/parser resource exposure and cross-window confusion.
They do not authenticate users, remove provider processing risks, prove an image
safe for every downstream decoder, or eliminate indirect prompt injection.

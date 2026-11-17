# Offline rendering assets

These pinned UMD bundles are embedded into self-contained HTML exports. They do
not require npm, Python dependencies, a server, or network access at runtime.

| Package | Version | Package source | License |
| --- | --- | --- | --- |
| Mermaid | 11.12.0 | https://registry.npmjs.org/mermaid/-/mermaid-11.12.0.tgz | MIT, `mermaid.LICENSE` |
| markdown-it | 14.1.0 | https://registry.npmjs.org/markdown-it/-/markdown-it-14.1.0.tgz | MIT, `markdown-it.LICENSE` |

`manifest.json` records the exact package member and SHA256 for every bundle and
license. Rendering verifies those hashes before embedding assets. Source bundles
are used unmodified on disk; HTML serialization escapes closing script tags.

To update, select an explicit upstream version, retrieve its package from the
official npm registry, extract the full UMD distribution and license without
executing package scripts, and update hashes/provenance. Run presentation tests,
including the Chromium offline/security check, and inspect representative output.
Do not substitute ESM distributions that fetch chunks or a CDN at render time.

The exporter disables raw authored HTML, remote images and clickable links;
Mermaid uses strict security with authored configuration and URL directives
rejected. A restrictive Content Security Policy blocks connections and external
resources. Text and Mermaid source remain available when rendering is disabled
or fails. A valid rendered diagram is not proof of its behavioral correctness.

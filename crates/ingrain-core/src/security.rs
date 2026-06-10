const INJECTION_MARKERS: [&str; 6] = [
    "ignore previous instructions",
    "disregard previous instructions",
    "system prompt",
    "developer message",
    "you are now",
    "act as system",
];

const WITHHELD: &str =
    "[possible prompt-injection text withheld by Ingrain; inspect source event before trusting]";

pub fn sanitize_for_context(text: &str) -> String {
    let stripped = strip_invisible(text).trim().to_string();
    let redacted = redact_obvious_secrets(&stripped);
    if has_prompt_injection_marker(&redacted) {
        WITHHELD.to_string()
    } else {
        redacted
    }
}

fn strip_invisible(text: &str) -> String {
    text.chars()
        .filter(|ch| !matches!(ch, '\u{200b}' | '\u{200c}' | '\u{200d}' | '\u{feff}'))
        .collect()
}

fn has_prompt_injection_marker(text: &str) -> bool {
    let lower = text.to_lowercase();
    INJECTION_MARKERS
        .iter()
        .any(|marker| lower.contains(marker))
}

fn redact_obvious_secrets(text: &str) -> String {
    let mut output = String::with_capacity(text.len());
    let mut token = String::new();

    for ch in text.chars() {
        if ch.is_whitespace() {
            if !token.is_empty() {
                output.push_str(&redact_secret_token(&token));
                token.clear();
            }
            output.push(ch);
        } else {
            token.push(ch);
        }
    }

    if !token.is_empty() {
        output.push_str(&redact_secret_token(&token));
    }

    output
}

fn redact_secret_token(token: &str) -> String {
    let lower = token.to_lowercase();
    if lower.starts_with("sk-")
        || lower.starts_with("ghp_")
        || lower.starts_with("xoxb-")
        || lower.starts_with("xoxa-")
        || lower.starts_with("xoxp-")
        || lower.starts_with("xoxr-")
        || lower.starts_with("xoxs-")
    {
        return "<redacted-secret>".to_string();
    }

    for marker in [
        "api_key", "api-key", "apikey", "secret", "token", "password",
    ] {
        if lower.starts_with(marker) && token.len() >= marker.len() + 17 {
            if let Some(separator) = token.find(['=', ':']) {
                let key = &token[..separator];
                return format!("{key}=<redacted>");
            }
        }
    }

    token.to_string()
}

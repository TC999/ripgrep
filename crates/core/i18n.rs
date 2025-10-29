/*!
Provides internationalization (i18n) support for ripgrep.

This module uses the Fluent localization system to provide translations
of help text and user-facing messages. It detects the user's preferred
locale from environment variables and loads the appropriate translation
resources.
*/

use std::fs;
use std::path::PathBuf;
use std::sync::OnceLock;

use fluent_bundle::{concurrent::FluentBundle, FluentResource};
use fluent_langneg::{negotiate_languages, NegotiationStrategy};
use unic_langid::{langid, LanguageIdentifier};

/// Static storage for the global localization bundle.
static LOCALES: OnceLock<Localization> = OnceLock::new();

/// Holds the localization resources and bundle.
pub struct Localization {
    bundle: FluentBundle<FluentResource>,
    #[allow(dead_code)]
    locale: LanguageIdentifier,
}

impl Localization {
    /// Create a new Localization instance by detecting the user's locale.
    fn new() -> Self {
        let requested = get_requested_locales();
        let available = get_available_locales();
        
        let default_locale = langid!("en-US");
        let supported = negotiate_languages(
            &requested,
            &available,
            Some(&default_locale),
            NegotiationStrategy::Filtering,
        );
        
        let locale = supported.first()
            .map(|&l| l.clone())
            .unwrap_or_else(|| default_locale.clone());
        
        let mut bundle = FluentBundle::new_concurrent(vec![locale.clone()]);
        
        // Load the fluent resources for the selected locale
        if let Some(resource) = load_locale_resource(&locale) {
            if let Err(errors) = bundle.add_resource(resource) {
                eprintln!("Failed to add resource: {:?}", errors);
            }
        }
        
        Self { bundle, locale }
    }
    
    /// Get a localized message by its ID.
    pub fn get_message(&self, id: &str) -> Option<String> {
        let msg = self.bundle.get_message(id)?;
        let pattern = msg.value()?;
        let mut errors = vec![];
        let value = self.bundle.format_pattern(pattern, None, &mut errors);
        
        if !errors.is_empty() {
            eprintln!("Localization errors for '{}': {:?}", id, errors);
        }
        
        Some(value.to_string())
    }
    
    /// Get the current locale.
    #[allow(dead_code)]
    pub fn locale(&self) -> &LanguageIdentifier {
        &self.locale
    }
}

/// Get the requested locales from environment variables.
fn get_requested_locales() -> Vec<LanguageIdentifier> {
    // Check multiple environment variables in order of preference:
    // 1. RG_LANG (ripgrep-specific)
    // 2. LC_ALL (overrides all other locale settings)
    // 3. LC_MESSAGES (for messages specifically)
    // 4. LANG (general locale setting)
    
    let env_vars = ["RG_LANG", "LC_ALL", "LC_MESSAGES", "LANG"];
    
    for var in &env_vars {
        if let Ok(value) = std::env::var(var) {
            // Parse the locale string (e.g., "en_US.UTF-8" -> "en-US")
            if let Some(locale_str) = value.split('.').next() {
                let locale_str = locale_str.replace('_', "-");
                if let Ok(langid) = locale_str.parse::<LanguageIdentifier>() {
                    return vec![langid];
                }
            }
        }
    }
    
    // Default to English if no locale found
    vec![langid!("en-US")]
}

/// Get the list of available locales by checking the locales directory.
fn get_available_locales() -> Vec<LanguageIdentifier> {
    let mut locales = vec![langid!("en-US")]; // Always include English
    
    // Try to read from embedded locales or filesystem
    if let Some(locales_dir) = get_locales_dir() {
        if let Ok(entries) = fs::read_dir(locales_dir) {
            for entry in entries.flatten() {
                if let Ok(file_type) = entry.file_type() {
                    if file_type.is_dir() {
                        if let Some(name) = entry.file_name().to_str() {
                            let locale_str = name.replace('_', "-");
                            if let Ok(langid) = locale_str.parse::<LanguageIdentifier>() {
                                if langid != langid!("en-US") {
                                    locales.push(langid);
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    locales
}

/// Get the locales directory path.
fn get_locales_dir() -> Option<PathBuf> {
    // First try to find locales relative to the executable
    if let Ok(exe) = std::env::current_exe() {
        if let Some(exe_dir) = exe.parent() {
            let locales_path = exe_dir.join("locales");
            if locales_path.exists() {
                return Some(locales_path);
            }
        }
    }
    
    // Try relative to current directory (for development)
    let locales_path = PathBuf::from("locales");
    if locales_path.exists() {
        return Some(locales_path);
    }
    
    None
}

/// Load the Fluent resource for a given locale.
fn load_locale_resource(locale: &LanguageIdentifier) -> Option<FluentResource> {
    let locales_dir = get_locales_dir()?;
    let locale_str = locale.to_string();
    let ftl_path = locales_dir.join(&locale_str).join("main.ftl");
    
    let content = fs::read_to_string(&ftl_path).ok()?;
    FluentResource::try_new(content).ok()
}

/// Initialize the global localization system.
pub fn init() {
    LOCALES.get_or_init(Localization::new);
}

/// Get a localized message by its ID.
///
/// If the message ID is not found or localization is not initialized,
/// returns None.
pub fn get_message(id: &str) -> Option<String> {
    LOCALES.get()?.get_message(id)
}

/// Get a localized message by its ID, with a fallback default.
///
/// If the message ID is not found, returns the provided default value.
#[allow(dead_code)]
pub fn get_message_or(id: &str, default: &str) -> String {
    get_message(id).unwrap_or_else(|| default.to_string())
}

/// Get the current locale.
#[allow(dead_code)]
pub fn current_locale() -> Option<&'static LanguageIdentifier> {
    LOCALES.get().map(|l| l.locale())
}

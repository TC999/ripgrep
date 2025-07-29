/*!
Internationalization support for ripgrep.

This module provides localization functionality using the fluent localization system.
*/

use i18n_embed::{
    fluent::{fluent_language_loader, FluentLanguageLoader},
    LanguageLoader,
};
use once_cell::sync::Lazy;
use rust_embed::RustEmbed;

#[derive(RustEmbed)]
#[folder = "i18n/"]
struct Localizations;

pub static LANGUAGE_LOADER: Lazy<FluentLanguageLoader> = Lazy::new(|| {
    let loader = fluent_language_loader!();
    
    // Load the language files
    loader.load_fallback_language(&Localizations).expect("Error while loading fallback language");
    
    // Try to load languages based on system locale
    let requested_languages = requested_languages();
    let requested_refs: Vec<&unic_langid::LanguageIdentifier> = requested_languages.iter().collect();
    if let Err(error) = loader.load_languages(&Localizations, &requested_refs) {
        eprintln!("Error while loading language for locale: {}", error);
    }
    
    loader
});

/// Get the list of requested languages from environment variables
fn requested_languages() -> Vec<unic_langid::LanguageIdentifier> {
    let mut languages = Vec::new();
    
    // Check standard environment variables for language preference
    if let Ok(lang) = std::env::var("LANG") {
        // Parse locale like "zh_CN.UTF-8" to get language identifier
        let lang_code = lang.split('.').next().unwrap_or(&lang);
        if let Ok(langid) = lang_code.parse() {
            languages.push(langid);
        }
    }
    
    if let Ok(lc_all) = std::env::var("LC_ALL") {
        let lang_code = lc_all.split('.').next().unwrap_or(&lc_all);
        if let Ok(langid) = lang_code.parse() {
            languages.push(langid);
        }
    }
    
    // Add fallback
    if languages.is_empty() {
        if let Ok(langid) = "en-US".parse() {
            languages.push(langid);
        }
    }
    
    languages
}

// Re-export the fl! macro for use in other modules
pub use i18n_embed_fl::fl;
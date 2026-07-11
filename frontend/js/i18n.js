const I18n = (() => {
    let _strings = {};
    let _lang = localStorage.getItem("lang") || "es";

    async function load(lang) {
        const res = await fetch(`/locales/${lang}.json`);
        _strings = await res.json();
        _lang = lang;
        localStorage.setItem("lang", lang);
        document.documentElement.lang = lang;
    }

    function t(key) {
        return _strings[key] ?? key;
    }

    function currentLang() {
        return _lang;
    }

    return { load, t, currentLang };
})();

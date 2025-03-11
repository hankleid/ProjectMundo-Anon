// Returns (promise) the languages catalog.
async function get_lang_dict() {
    return await fetch('/ProjectMundo-Anon/lang.json')
        .then(function(response) {
            return response.json();
        });
}

// Returns (promise) the articles catalog.
async function get_articles_dict() {
    return await fetch('/ProjectMundo-Anon/articles.json')
        .then(function(response) {
            return response.json();
        });
}

// Adds an anchor element to the parent node.
function gen_entry(parent, link, lang, name) {
    let lang_el = document.createElement("a");
    lang_el.setAttribute("href", link);
    lang_el.setAttribute("id", lang);
    lang_el.innerHTML = name;
    parent.appendChild(lang_el);
}

function configureDropdown(doi, lang) {
    // params: doi, lang
    // called from index or another article page
    // configure the dropdown langs to have data-doi = doi
    // update the dropdown button with the current language

    console.log(lang);
    let dropdown = document.getElementById("lang-dropdown");

    // Remove all the languages in the dropdown.
    while (dropdown.lastElementChild) { dropdown.removeChild(dropdown.lastElementChild); }

    // Repopulate the dropdown menu.
    get_lang_dict().then(function(lang_data) {
        let dropdown_button = document.getElementById("btn-dropdown");
        dropdown_button.innerHTML = lang_data.codes[lang]+' <i class="fa fa-caret-down"></i>';

        all_langs = Object.keys(lang_data.codes);

        // Determine the languages with which to populate the dropdown.
        get_articles_dict().then(function(article_data) {
            for (let i = 0; i < all_langs.length; i++) {
                if (doi == "index") {
                    link = "/ProjectMundo-Anon/index/" + all_langs[i] + ".html";
                    gen_entry(dropdown, link, all_langs[i], lang_data.codes[all_langs[i]]);

                } else if (Object.keys(article_data[doi]['langs']).includes(all_langs[i])) {
                    // doi
                    link = "/ProjectMundo-Anon/articles/" + doi + "/" + all_langs[i] + ".xml";
                    gen_entry(dropdown, link, all_langs[i], lang_data.codes[all_langs[i]]);
                }
            }
        });
    });
    
    // Update the home link to correct language.
    let home = document.getElementById("home");
    home.setAttribute("href", "/ProjectMundo-Anon/index/" + lang + ".html");

    // Refresh the search event listener.
    document.getElementById("search-txt").addEventListener("keydown", function(event) {
        if (event.key === 'Enter') {
            search()
        }
    });
}

/* When the user clicks on the button, 
toggle between hiding and showing the dropdown content */
function dropDown() {
    document.getElementById("lang-dropdown").classList.toggle("show");
}

function search() {
    get_articles_dict().then(function(article_data) {
        let s = document.getElementById("search-txt").value;
        let found = false;

        keys = Object.keys(article_data);
        for (let i = 0; i < keys.length; i++) {
            if (s == article_data[keys[i]]['meta']['doi']) {
                found = true;
                window.location.href = "/ProjectMundo-Anon/articles/" + keys[i] + "/eng.xml";
            }
        }

        if (!found) {
            console.log("not found :(");
        }
    });
}

// Close the dropdown if the user clicks outside of it
window.onclick = function(e) {
    if (!e.target.matches('.dropbtn')) {
    var myDropdown = document.getElementById("lang-dropdown");
        if (myDropdown.classList.contains('show')) {
        myDropdown.classList.remove('show');
        }
    }
}
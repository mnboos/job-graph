import "./assets/main.css";

import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { Quasar } from "quasar";
import quasarLang from "quasar/lang/de-CH";
import quasarIconSet from "quasar/icon-set/material-symbols-sharp";
import { VueQueryPlugin } from "@tanstack/vue-query";
import { Configuration, DefaultConfig, type Middleware, type RequestContext } from "@/api";

// Import icon libraries
import "@quasar/extras/material-symbols-sharp/material-symbols-sharp.css";

// Import Quasar css
import "quasar/dist/quasar.css";
import { getCookie, useBackendHost } from "@/utils";

const app = createApp(App);

/**
 * Small middleware to add appropriate headers depending on the HTTP method
 * before starting the API call.
 */
export class AppropriateOptionsMiddleware implements Middleware {
    /**
     * Called before executing the request.
     * @param context
     */
    pre(context: RequestContext) {
        const init = context.init;

        const currentHeaders =
            Array.isArray(init.headers) || init.headers instanceof Headers
                ? Object.fromEntries(init.headers)
                : init.headers;

        context.init = {
            ...init,
            headers: {
                ...currentHeaders,
                "X-CSRFToken": getCookie("csrftoken") ?? "",
                "Content-Type": "application/json",
            },
        };
        return Promise.resolve({ url: context.url, init: context.init });
    }
}

const backendHost = useBackendHost();
DefaultConfig.config = new Configuration({
    basePath: backendHost,
    credentials: "include",
    middleware: [new AppropriateOptionsMiddleware()],
});

app.use(router);
app.use(VueQueryPlugin);
app.use(Quasar, {
    plugins: {}, // import Quasar plugins and add here
    lang: quasarLang,
    iconSet: quasarIconSet,
});

app.mount("#app");

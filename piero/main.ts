import { createPieroApp } from '@giro3d/piero';
import { CityJSONLoader, IFCLoader, PLYLoader, PotreeLoader, Tour } from '@giro3d/piero/modules';

import DefaultConfig from './config';
import styles from './styles';

async function start(): Promise<void> {
    // The base URL will be used to resolve all relative URLs, (e.g URLs that points to the public/ folder)
    const baseUrl = import.meta.env.VITE_PROD ? import.meta.env.VITE_BASE_URL : 'http://localhost:8080/';

    // The list of all optional modules we want to use.
    // Since this is the default Piero app, we load all the modules
    // for demonstration purposes. However, in a customized Piero app,
    // you will want to select as few modules as possible for the best
    // performance and bundle size.
    const modules = [
        new Tour(),
        new IFCLoader(),
        new CityJSONLoader(),
        new PLYLoader(),
        new PotreeLoader(),
    ];

    // Piero can either load a remote configuration from the provided 'config' URL param
    // i.e: http://piero.giro3d.org?config=my-remote-configuration.json
    // or load the static configuration file (config.ts) in the same folder as this file.
    

    // Always use remote configuration by default
    // const configurationUrl = "http://localhost/configuration.json";

    const isProd = import.meta.env.VITE_PROD;
    console.log(isProd);
    
    const base_url_env = import.meta.env.VITE_API_BASE_URL
    console.log(base_url_env);

    const apiBaseUrl = import.meta.env.VITE_PROD ? import.meta.env.VITE_API_BASE_URL : 'http://localhost:8000';
    console.log(apiBaseUrl);
    const externalConfig = apiBaseUrl + "/api/piero-config"

    const params = new URLSearchParams(document.location.search);
    const configurationUrl = params.get('config');
    // const configuration = configurationUrl ?? DefaultConfig;
    const configuration = externalConfig;

    // We are now ready to instantiate Piero on the #app DOM element of our webpage.
    return createPieroApp({
        baseUrl,
        configuration,
        container: '#app',
        dynamicStyles: styles,
        modules,
    });
}

start().catch(console.error);

import {AbstractSDC, app} from 'sdc_client';


/**
 * Help page about preprocess scripts that a Shuttle runs on each file before sending it.
 *
 * - Static text; no data is shown or changed. Requires login.
 * - Explains the script folder (`~/shuttle/scripts` on Linux, `%USERPROFILE%\shuttle\scripts` on Windows) and how scripts are run.
 * - Offers downloads of the "ShuttleFromContentRenamer" script and of the ChemConverterApp (Linux and Windows).
 * - The ChemConverter is not a script; it is enabled with `with_converter` in `<shuttle-instance-edit>`.
 */
class ShuttleScriptsController extends AbstractSDC {

    constructor() {
        super();
        this.contentUrl = "/sdc_view/main_app/shuttle_scripts"; //<shuttle-scripts></shuttle-scripts>

        /**
         * Uncomment the following line to make sure the HTML template
         * of this controller is not cached and reloaded for every instance
         * of this controller.
         */
        // this.contentReload = true;

        /**
         * Uncomment the following line to make this controller asynchronous.
         * This means that the parent controller finishes loading without
         * waiting for this controller
         */
        // this.load_async = true;

        /**
         * Events is an array of dom events.
         * The pattern is {'event': {'dom_selector': handler}}
         * Uncomment the following line to add events;
         */
        // this.events.unshift({'click': {'.header-sample': (ev, $elem)=> $elem.css('border', '2px solid black')}});
    }

    //-------------------------------------------------//
    // Lifecycle handler                               //
    // - onInit (tag parameter)                        //
    // - onLoad (DOM not set)                          //
    // - willShow  (DOM set)                           //
    // - onRefresh  (recalled on reload)              //
    //-------------------------------------------------//
    // - onRemove                                      //
    //-------------------------------------------------//

    onLoad($html) {
        return super.onLoad($html);
    }

    willShow() {
        return super.willShow();
    }

    onRefresh() {
        return super.onRefresh();
    }

}

app.register(ShuttleScriptsController, false);
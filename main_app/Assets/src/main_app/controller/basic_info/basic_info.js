import {AbstractSDC, app} from 'sdc_client';


/**
 * Start page of the ShuttleBuilder: explains what a Shuttle is and how to install one.
 *
 * - Static help text; no data is shown or changed. No login required.
 * - Describes the workflow: create a Shuttle in `<shuttle-instance-list>`, download the executable, install it on the lab PC.
 * - Contains install steps for Windows, Windows XP with SFTP and Linux (systemd), with links to the needed helper files.
 * - Links to `<shuttle-scripts>` for preprocess scripts, the OpenAPI file and the Chemotion documentation.
 */
class BasicInfoController extends AbstractSDC {

    constructor() {
        super();
        this.contentUrl = "/sdc_view/main_app/basic_info"; //<basic-info></basic-info>

        /**
         * Events is an array of dom events.
         * The pattern is {'event': {'dom_selector': handler}}
         * Uncommend the following line to add events;
         */
        // this.events.unshift({'click': {'.header-sample': (ev, $elem)=> $elem.css('border', '2px solid black')}}});
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

app.register(BasicInfoController);
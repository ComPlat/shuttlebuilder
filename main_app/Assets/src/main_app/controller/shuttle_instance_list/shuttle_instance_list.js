import {AbstractSDC, app} from 'sdc_client';


/**
 * List of the user's Shuttle instances (staff see all), with search, download and management actions.
 *
 * - Download builds the executable for that instance from the active git repo and downloads it; this may take a while.
 *   Result: the bare executable, a ZIP with WinSCP (Windows i386 + SFTP), or a ZIP with ChemConverter and the profile (with converter).
 * - The wrench opens `<shuttle-instance-edit>` for the instance; "Copy" opens it prefilled as a new copy.
 * - The trash button deletes the instance and its build files after a confirm dialog; this cannot be undone.
 * - "NEW" opens `<shuttle-instance-edit>` to create one.
 * - Shows the active git repo; if none is linked the list is not shown. Requires login.
 */
class ShuttleInstanceListController extends AbstractSDC {

    constructor() {
        super();
        this.contentReload = true;
        this.contentUrl = "/sdc_view/main_app/shuttle_instance_list"; //<shuttle-instance-list></shuttle-instance-list>

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
        this.model = this.newModel('ShuttleInstance');
        return super.onLoad($html);
    }

    willShow() {
        return super.willShow();
    }

    onRefresh() {
        return super.onRefresh();
    }

}

app.register(ShuttleInstanceListController).addMixin('sdc-list-view');
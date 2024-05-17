import {AbstractSDC, app} from 'sdc_client';


class GitInstanceListController extends AbstractSDC {

    constructor() {
        super();
        this.contentUrl = "/sdc_view/main_app/git_instance_list"; //<git-instance-list></git-instance-list>

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

    onInit() {
        this.model = this.newModel('GitInstance');
    }

    onLoad($html) {
        return super.onLoad($html);
    }

    willShow() {
        return super.willShow();
    }

    onRefresh() {
        return super.onRefresh();
    }

    activate_form(data) {
        return this._form_manager(data.pk, 'acivate');
    }

    reload_form(data) {
        return this._form_manager(data.pk, 'reload');
    }

    _form_manager(pk, type) {
        let self = this;
        const btnTitle = type === 'reload' ? 'Reload' : 'Activate';
        const btnHint = type === 'reload' ? 'Reload the repo!' : 'Activate mapping. Only one can be active!';
        const $mls = self.find('.main-loading-screen');

        function activate_update(btn) {
            $mls.show();
            self.serverCall('activate_git', {'pk': pk}).then(() => {
                $mls.hide();
            }).catch((res) => {
                $mls.hide();
            });
        }

        return <span>
            <button type="button" data-bs-toggle="tooltip" data-bs-placement="left"
                    title={btnHint} className="btn btn-info" onClick={function () {
                activate_update(this);
            }}>
                {btnTitle}
            </button>
        </span>
    }

}

app.register(GitInstanceListController).addMixin('sdc-list-view');
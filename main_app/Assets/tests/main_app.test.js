/**
 * @jest-environment jsdom
 */

import {test_utils} from 'sdc_client';
import {} from "#root/src/main_app/main_app.organizer.js";
import '#root/src/sdc_tools/sdc_tools.organizer.js'
import '#root/src/sdc_user/sdc_user.organizer.js'

describe('BasicInfo', () => {
    let controller;

    beforeEach(async () => {
        // Create new controller instance based on the standard process.
        controller = await test_utils.get_controller('basic-info',
                                                  {},
                                                  '<div><h1>Controller Loaded</h1></div>');
    });

    test('Load Content', async () => {
        const $div = $('body').find('basic-info');
        expect($div.length).toBeGreaterThan(0);
    });

});

describe('GitInstanceList', () => {
    let controller;

    beforeEach(async () => {
        // Create new controller instance based on the standard process.
        controller = await test_utils.get_controller('git-instance-list',
                                                  {},
                                                  '<div><h1>Controller Loaded</h1></div>');
    });

    test('Load Content', async () => {
        const $div = $('body').find('git-instance-list');
        expect($div.length).toBeGreaterThan(0);
    });

});

describe('GitInsatnceEdit', () => {
    let controller;

    beforeEach(async () => {
        // Create new controller instance based on the standard process.
        controller = await test_utils.get_controller('git-insatnce-edit',
                                                  {},
                                                  '<div><h1>Controller Loaded</h1></div>');
    });

    test('Load Content', async () => {
        const $div = $('body').find('git-insatnce-edit');
        expect($div.length).toBeGreaterThan(0);
    });

});

describe('ShuttleInstanceList', () => {
    let controller;

    beforeEach(async () => {
        // Create new controller instance based on the standard process.
        controller = await test_utils.get_controller('shuttle-instance-list',
                                                  {},
                                                  '<div><h1>Controller Loaded</h1></div>');
    });

    test('Load Content', async () => {
        const $div = $('body').find('shuttle-instance-list');
        expect($div.length).toBeGreaterThan(0);
    });

});

describe('ShuttleInstanceEdit', () => {
    let controller;

    beforeEach(async () => {
        // Create new controller instance based on the standard process.
        controller = await test_utils.get_controller('shuttle-instance-edit',
                                                  {},
                                                  '<div><h1>Controller Loaded</h1></div>');
    });

    test('Load Content', async () => {
        const $div = $('body').find('shuttle-instance-edit');
        expect($div.length).toBeGreaterThan(0);
    });

});
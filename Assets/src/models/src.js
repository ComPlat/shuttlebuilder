import ShuttleInstance from './ShuttleInstance.js';
import GitInstance from './GitInstance.js';
import ElnConnection from './ElnConnection.js';
import ElnUser from './ElnUser.js';
import SdcUser from './SdcUser.js';
import { registerModel } from 'sdc_client';

registerModel("SdcUser", SdcUser);
registerModel("ElnUser", ElnUser);
registerModel("ElnConnection", ElnConnection);
registerModel("GitInstance", GitInstance);
registerModel("ShuttleInstance", ShuttleInstance);
import React from 'react';
import { BadgeColor } from '../../../../Constant';
import CommonHeaderClass from '../Common/CommonHeaderClass';

const BadgeColorCard = () => {
  return (
    <CommonHeaderClass title={BadgeColor}>{`.badge-primary {
        background-color: #7366ff;
        }
        .badge-secondary {
        background-color: #f73164;
        }
        .badge-success {
        background-color: #51bb25;
        }
        .badge-danger {
        background-color: #dc3545;
        }
        .badge-info {
        background-color: #a927f9;
        }
        .badge-light {
        background-color: #f4f4f4;
        }
        .badge-dark {
        background-color: #2c323f;
        }
        .badge-warning {
        background-color: #f8d62b;
        }
      `}
    </CommonHeaderClass>

  );
};

export default BadgeColorCard;
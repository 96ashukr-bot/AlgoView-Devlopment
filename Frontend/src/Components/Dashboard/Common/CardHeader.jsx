import React from 'react';
import { CardHeader } from 'reactstrap';
import { H5 } from '../../../AbstractElements';

const CardHeaderCommon = ({ title, options }) => {
  return (
    <CardHeader>
      <div className="header-top">
        <H5 attrH5={{ className: "m-0" }} >{title}</H5>
        <div className="card-header-right-icon">
          <select className="button btn btn-primary">
            {options && options.map((data, i) =>
              (<option key={i}>{data}</option>)
            )}
          </select>
        </div>
      </div>
    </CardHeader>);
};

export default CardHeaderCommon;
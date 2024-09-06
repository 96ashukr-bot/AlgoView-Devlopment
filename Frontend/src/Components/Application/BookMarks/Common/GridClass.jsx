import React, { Fragment } from 'react';
import { H6, LI, UL } from '../../../../AbstractElements';
import { Grid, List } from 'react-feather';
import { CardHeader } from 'reactstrap';

const GridClass = ({ title, callback }) => {
  const Gridbookmark = () => {
    callback(true);
  };
  const Listbookmark = () => {
    callback(false);
  };

  return (
    <Fragment>
      <CardHeader className='d-flex'>
        <H6 attrH6={{ className: 'mb-0' }}>{title}</H6>
        <UL attrUL={{ className: 'simple-list flex-row' }}>
          <LI attrLI={{ className: 'border-0' }}>
            <a className='border-0 grid-bookmark-view' href='#javascript'>
              <Grid onClick={Gridbookmark} />
            </a>
          </LI>
          <LI attrLI={{ className: 'border-0' }}>
            <a className='border-0 list-layout-view' href='#javascript'>
              <List onClick={Listbookmark} />
            </a>
          </LI>
        </UL>
      </CardHeader>
    </Fragment>
  );
};

export default GridClass;

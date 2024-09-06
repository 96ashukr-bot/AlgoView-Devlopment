import React, { Fragment } from 'react';
import PrintComponent from './Print';
import { Breadcrumbs } from '../../../../AbstractElements';

const InvoiceContain = () => {
  return (
    <Fragment>
      <Breadcrumbs parent='Ecommerce' title='Invoice' mainTitle='Invoice' />
      <PrintComponent />
    </Fragment>
  );
};
export default InvoiceContain;

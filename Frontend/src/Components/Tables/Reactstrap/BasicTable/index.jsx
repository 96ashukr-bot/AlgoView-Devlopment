import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import BasicTableClass from './BasicTableClass';
import InverseTableClass from './InverseTableClass';
import HoverableRowsClass from './HoverableRows';
import ContextualClasses from './ContextualClasses';
import StripedRowClass from './StripedRowClass';
import StripeInverseClass from './StripInverseClass';
import CaptionClass from './Caption';
import ResponsiveClass from './ResponsiveClass';
import BreckpointClass from './BreckpointClass';
import TableHeadClass from './TableHeadClass';
import InversePrimaryClass from './InversTableClass';
import { Breadcrumbs } from '../../../../AbstractElements';
import CustomHoverClass from './CustomeHover';
import DashedBorderClass from './DashedBorderClass';
const BasicTables = () => {
  return (
    <Fragment>
      <Breadcrumbs parent='Tables' title='Basic Tables' mainTitle='Basic Tables' />
      <Container fluid={true}>
        <Row>
          <BasicTableClass />
          <InverseTableClass />
          <HoverableRowsClass />
          <InversePrimaryClass />
          <ContextualClasses />
          <TableHeadClass />
          <StripedRowClass />
          <StripeInverseClass />
          <CaptionClass />
          <ResponsiveClass />
          <BreckpointClass />
          <CustomHoverClass />
          <DashedBorderClass />
        </Row>
      </Container>
    </Fragment>
  );
};

export default BasicTables;

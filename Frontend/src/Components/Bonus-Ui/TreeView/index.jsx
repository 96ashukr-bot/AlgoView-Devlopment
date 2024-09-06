import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import BasicTree from './BasicTree';
import CheckboxTree from './CheckboxTree';
import ContextmenuTree from './ContextmenuTree';
import DragTree from './DragTree';

const TreeView = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Tree View' parent='Bonus Ui' title='Tree View' />
      <Container fluid={true}>
        <Row>
          <BasicTree />
          <CheckboxTree />
          <DragTree />
          <ContextmenuTree />
        </Row>
      </Container>
    </Fragment>
  );
};

export default TreeView;

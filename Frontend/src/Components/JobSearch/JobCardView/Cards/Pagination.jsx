import { LI, UL } from '../../../../AbstractElements';
import React, { Fragment } from 'react';
import { Col } from 'reactstrap';

const Pagination = () => {
  return (
    <Fragment>
      <Col xs='12'>
        <nav aria-label='...'>
          <UL attrUL={{ className: 'pagination pagination-primary justify-content-end simple-list d-flex flex-row' }}>
            <LI attrLI={{ className: 'page-item disabled border-0' }}>
              <a className='page-link' href='#javascript' tabIndex='-1'>
                Previous
              </a>
            </LI>
            <LI attrLI={{ className: 'page-item border-0' }}>
              <a className='page-link' href='#javascript'>
                1
              </a>
            </LI>
            <LI attrLI={{ className: 'page-item active border-0' }}>
              <a className='page-link' href='#javascript'>
                2 <span className='sr-only'>(current)</span>
              </a>
            </LI>
            <LI attrLI={{ className: 'page-item border-0' }}>
              <a className='page-link' href='#javascript'>
                3
              </a>
            </LI>
            <LI attrLI={{ className: 'page-item border-0' }}>
              <a className='page-link' href='#javascript'>
                Next
              </a>
            </LI>
          </UL>
        </nav>
      </Col>
    </Fragment>
  );
};
export default Pagination;

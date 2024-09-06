import React, { Fragment, useState } from 'react';
import { UL, LI } from '../../../../AbstractElements';
import Sorting from './Sorting';
import { ChevronDown, Grid, List } from 'react-feather';
import { Col, Row } from 'reactstrap';
import { useContext } from 'react';
import FilterContext from '../../../../_helper/Ecommerce/Filter';

const ProductTotal = () => {
  const { setFilterContext } = useContext(FilterContext);
  const [filterSidebar, setFilterSidebar] = useState(true);
  const onFilterClick = () => {
    setFilterSidebar(!filterSidebar);
    setFilterContext(filterSidebar);
  };
  const gridLayout = () => {
    document.getElementById('product-wrapper-grid').classList.remove('list-view');

    var elems = document.getElementById('gridRow').childNodes;
    [].forEach.call(elems, function (el) {
      el.className = '';
      el.classList.add('col-xl-3');
      el.classList.add('col-sm-6');
      el.classList.add('xl-4');
    });
  };
  const listLayout = () => {
    document.getElementById('product-wrapper-grid').classList.add('list-view');
    var elems = document.getElementById('gridRow').childNodes;
    [].forEach.call(elems, function (el) {
      el.className = '';
      el.classList.add('col-xl-12');
    });
  };
  const LayoutView = (layoutColumns) => {
    if (!document.getElementById('product-wrapper-grid').classList.contains('list-view')) {
      var elems = document.getElementById('gridRow').childNodes;
      [].forEach.call(elems, function (el) {
        el.className = '';
        el.classList.add('col-xl-' + layoutColumns);
        el.classList.add('col-sm-' + layoutColumns);
      });
    }
  };
  return (
    <Fragment>
      <Row className='m-b-10'>
        <Col md='6' className='products-total'>
          <div className='square-product-setting d-inline-block'>
            <a className='icon-grid grid-layout-view' onClick={gridLayout} href='#javascript'>
              <Grid />
            </a>
          </div>
          <div className='square-product-setting d-inline-block '>
            <a className='icon-grid m-0 list-layout-view' onClick={listLayout} href='#javascript'>
              <List />
            </a>
          </div>
          <span className='d-none-productlist filter-toggle' onClick={() => onFilterClick()}>
            Filters
            <span className='ms-2'>
              <ChevronDown className=' toggle-data' />
            </span>
          </span>
          <div className='grid-options d-inline-block'>
            <UL attrUL={{ className: 'list-group', as: 'ul' }}>
              <LI attrLI={{ className: 'border-0' }}>
                <a className='product-2-layout-view' onClick={() => LayoutView(6)} href='#javascript'>
                  <span className='line-grid line-grid-1 bg-primary'></span>
                  <span className='line-grid line-grid-2 bg-primary'></span>
                </a>
              </LI>
              <LI attrLI={{ className: 'border-0' }}>
                <a className='product-3-layout-view' onClick={() => LayoutView(4)} href='#javascript'>
                  <span className='line-grid line-grid-3 bg-primary'></span>
                  <span className='line-grid line-grid-4 bg-primary'></span>
                  <span className='line-grid line-grid-5 bg-primary'></span>
                </a>
              </LI>
              <LI attrLI={{ className: 'border-0' }}>
                <a className='product-4-layout-view' onClick={() => LayoutView(3)} href='#javascript'>
                  <span className='line-grid line-grid-6 bg-primary'></span>
                  <span className='line-grid line-grid-7 bg-primary'></span>
                  <span className='line-grid line-grid-8 bg-primary'></span>
                  <span className='line-grid line-grid-9 bg-primary'></span>
                </a>{' '}
              </LI>
              <LI attrLI={{ className: 'border-0' }}>
                <a className='product-6-layout-view' onClick={() => LayoutView(2)} href='#javascript'>
                  <span className='line-grid line-grid-10 bg-primary'></span>
                  <span className='line-grid line-grid-11 bg-primary'></span>
                  <span className='line-grid line-grid-12 bg-primary'></span>
                  <span className='line-grid line-grid-13 bg-primary'></span>
                  <span className='line-grid line-grid-14 bg-primary'></span>
                  <span className='line-grid line-grid-15 bg-primary'></span>
                </a>
              </LI>
            </UL>
          </div>
        </Col>
        <Sorting />
      </Row>
    </Fragment>
  );
};
export default ProductTotal;

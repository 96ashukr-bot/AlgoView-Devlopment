import { Featured, HighestPrices, LowestPrices, ShowingProducts } from '../../../../Constant';
import FilterContext from '../../../../_helper/Ecommerce/Filter';
import React, { Fragment, useContext } from 'react';
import { Col, Input } from 'reactstrap';

const Sorting = () => {
  const { filterSortBy } = useContext(FilterContext);
  const filterSortFunc = (event) => {
    filterSortBy(event);
  };
  return (
    <Fragment>
      <Col md='6' className='text-sm-end'>
        <span className='f-w-600 m-r-5'>{ShowingProducts}</span>
        <div className='select2-drpdwn-product select-options d-inline-block' onChange={(e) => filterSortFunc(e.target.value)}>
          <Input className='form-control btn-square' type='select' name='select'>
            <option value='Featured'>{Featured}</option>
            <option value='LowestPrices'>{LowestPrices}</option>
            <option value='HighestPrices'>{HighestPrices}</option>
          </Input>
        </div>
      </Col>
    </Fragment>
  );
};
export default Sorting;

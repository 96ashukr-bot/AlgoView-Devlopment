import { productColumns, productData } from '../../../../Data/Ecommerce/ProductList';
import React, { Fragment } from 'react';
import DataTable from 'react-data-table-component';

const ProductTableData = () => {
  return (
    <Fragment>
      <div className='table-responsive product-table'>
        <DataTable noHeader pagination paginationServer columns={productColumns} data={productData} highlightOnHover={true} striped={true} responsive={true} />
      </div>
    </Fragment>
  );
};
export default ProductTableData;

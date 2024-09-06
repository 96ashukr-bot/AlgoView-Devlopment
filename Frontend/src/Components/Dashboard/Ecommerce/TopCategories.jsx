import React from 'react';
import { Link } from 'react-router-dom';
import { Image, UL, LI, H6 } from '../../../AbstractElements';
import { TopCategoriesData } from '../../../Data/Ecommerce';

const TopCategories = () => {
  return (
    <UL attrUL={{ className: 'categories-list d-flex' }}>
      {TopCategoriesData.map((item, i) => (
        <LI key={i} attrLI={{ className: 'd-flex' }}>
          <div className='bg-light'>
            <Image attrImage={{ className: 'm-0', src: require(`../../../assets/images/dashboard-2/category/${item.image}`), alt: 'vector burger' }} />
          </div>
          <div>
            <H6 attrH6={{ className: 'mb-0' }}>
              <Link to={`/product`}>{item.title}</Link>
            </H6>
            <span className='f-light f-12 f-w-500'>({item.subTitle})</span>
          </div>
        </LI>
      ))}
    </UL>
  );
};

export default TopCategories;

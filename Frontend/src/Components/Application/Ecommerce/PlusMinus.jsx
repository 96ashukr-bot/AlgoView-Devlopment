import React, { Fragment, useState } from 'react';
import { Input } from 'reactstrap';
import { Btn } from '../../AbstractElements';

const PlusMinus = () => {
    const [quantity, setQuantity] = useState(1);
    const [stock, setStock] = useState('');
    const changeQty = (e) => {
        setQuantity(parseInt(e.target.value));
    };
    const plusQty = () => {
        if (quantity >= 1) {
            setQuantity(quantity + 1);
        } else {
            setStock('Out of Stock !');
        }
    };
    const minusQty = () => {
        if (quantity > 1) {
            setStock('InStock');
            setQuantity(quantity - 1);
        }
    };
    return (
        <Fragment>
            <div className="input-group bootstrap-touchspin">
                <Btn attrBtn={{ color: 'primary', className: 'bootstrap-touchspin-down', onClick: minusQty }}
                >
                    <i className="fa fa-minus"></i>
                </Btn>
                <Input className="touchspin text-center" type="text" name="quantity" value={quantity}
                    onChange={(e) => changeQty(e)}
                    style={{ display: 'block' }}
                />
                <Btn attrBtn={{
                    color: 'primary btn-square', className: 'bootstrap-touchspin-up', onClick: plusQty
                }}
                >
                    <i className="fa fa-plus"></i>
                </Btn>
            </div>
        </Fragment>
    );
};
export default PlusMinus;
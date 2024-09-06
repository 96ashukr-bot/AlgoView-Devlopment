import { ActiveButtons, Add, BasicButtonGroup, BootstrapStateButtons, CheckBoxButtonGroup, DangerButton, DefaultButtons, DisabledButtons, DisabledOutlineButtons, EdgesButtonGroup, ExtraSmallButtons, FlatButtonGroup, GradienButtons, InfoButton, LargeButtonGroup, LargeButtons, LargeEdgesButtonGroup, LightButton, OutlineButtonGroup, OutlineButtons, OutlineCustomButtonGroup, OutlineEdgesButton, OutlineExtraSmallButtons, OutlineFlatButton, OutlineLargeButtons, OutlineSmallButtons, PrimaryButton, RadioButtonGroup, SecondaryButton, SmallButtons, SuccessButton, WarningButton } from '../../../../Constant';

export const DefaultButtonData = [
    {
        title: DefaultButtons,
        span: BootstrapStateButtons,
        btnSub: [
            {
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                colorClass: 'info',
                title: InfoButton,
            },
            {
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: LargeButtons,
        span: Add,
        code: '.btn-lg',
        detail: 'class for large size buttons',
        cardId: 'large-btn',
        btnSub: [
            {
                size: 'lg',
                colorClass: 'primary',
                title: PrimaryButton
            },
            {
                size: 'lg',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'lg',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'lg',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'lg',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'lg',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'lg',
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: SmallButtons,
        span: Add,
        code: '.btn-sm',
        detail: 'class for small size buttons',
        cardId: 'small-btn',
        btnSub: [
            {
                size: 'sm',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'sm',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'sm',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'sm',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'sm',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'sm',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'sm',
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: ExtraSmallButtons,
        span: Add,
        code: '.btn-xs',
        detail: 'class for extra small size buttons',
        cardId: 'ex-small-btn',
        btnSub: [
            {
                size: 'xs',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'xs',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'xs',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'xs',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'xs',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'xs',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'xs',
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: ActiveButtons,
        span: Add,
        code: '.active',
        detail: 'class for active state',
        cardId: 'active-btn',
        btnSub: [
            {
                active: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                active: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                active: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                active: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                active: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                active: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                active: true,
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: DisabledButtons,
        span: Add,
        code: `.disabled class or disabled='disabled'`,
        detail: 'attribute for disabled button',
        cardId: 'disabled-btn',
        btnSub: [
            {
                disabled: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                disabled: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                disabled: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                disabled: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                disabled: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                disabled: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                disabled: true,
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: OutlineButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for border button',
        cardId: 'outline-button',
        btnSub: [
            {
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                outline: true,
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: OutlineLargeButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for outline and',
        code2: '.btn-lg',
        detail2: 'class for large button',
        cardId: 'outline-bold-button',
        btnSub: [
            {
                size: 'lg',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'lg',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'lg',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'lg',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'lg',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'lg',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'lg',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: OutlineSmallButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for outline and',
        code2: '.btn-sm',
        detail2: 'class for small button',
        cardId: 'outline-small-button',
        btnSub: [
            {
                size: 'sm',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'sm',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'sm',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'sm',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'sm',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'sm',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'sm',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: OutlineExtraSmallButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for outline and',
        code2: '.btn-xs',
        detail2: 'class for extra small button',
        cardId: 'ex-outline-small-button',
        btnSub: [
            {
                size: 'xs',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'xs',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'xs',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'xs',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'xs',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'xs',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'xs',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: DisabledOutlineButtons,
        span: Add,
        code1: `.disabled`,
        detail1: 'class or',
        code2: `disabled='disabled'}`,
        detail2: 'attribute for disabled state',
        cardId: 'ex-outline-small-button',
        btnSub: [
            {
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: GradienButtons,
        span: Add,
        code1: `.btn-*-gradien`,
        detail1: 'class for gradien button',
        cardId: 'gradiant',
        btnSub: [
            {
                colorClass: 'primary-gradien',
                title: PrimaryButton,
            },
            {

                colorClass: 'secondary-gradien',
                title: SecondaryButton,
            },
            {
                colorClass: 'success-gradien',
                title: SuccessButton,
            },
            {
                colorClass: 'info-gradien',
                title: InfoButton,
            },
            {
                colorClass: 'warning-gradien',
                title: WarningButton,
            },
            {
                colorClass: 'danger-gradien',
                title: DangerButton,
            },
            {
                colorClass: 'light-gradien',
                title: LightButton,
            }
        ]
    },
]


export const EdgeButtonData = [
    {
        title: DefaultButtons,
        span: 'Add',
        code: `.btn-pill`,
        detail: 'class for edge button',
        btnSub: [
            {
                btnClass: 'btn-pill',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill',
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: LargeButtons,
        span: 'Add',
        code: `.btn-pill & .btn-lg`,
        detail: 'class for large button',
        btnSub: [
            {
                size: 'lg',
                btnClass: 'btn-pill',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-pill',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-pill',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-pill',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-pill',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-pill',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-pill',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: SmallButtons,
        span: 'Add',
        code: `.btn-pill & .btn-sm`,
        detail: 'class for small button',
        btnSub: [
            {
                size: 'sm',
                btnClass: 'btn-pill',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-pill',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-pill',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-pill',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-pill',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-pill',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-pill',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: ExtraSmallButtons,
        span: 'Add',
        code: `.btn-pill & .btn-xs`,
        detail: 'class for extra small button',
        btnSub: [
            {
                size: 'xs',
                btnClass: 'btn-pill',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-pill',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-pill',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-pill',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-pill',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-pill',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-pill',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: ActiveButtons,
        span: 'Add',
        code: `.active`,
        detail: 'for active state',
        btnSub: [
            {
                active: true,
                btnClass: 'btn-pill',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                active: true,
                btnClass: 'btn-pill',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                active: true,
                btnClass: 'btn-pill',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                active: true,
                btnClass: 'btn-pill',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                active: true,
                btnClass: 'btn-pill',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                active: true,
                btnClass: 'btn-pill',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                active: true,
                btnClass: 'btn-pill',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: DisabledButtons,
        span: 'Add',
        code: `.disabled || disabled='disabled'`,
        detail: 'attribute for disabled button',
        btnSub: [
            {
                disabled: true,
                btnClass: 'btn-pill',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                disabled: true,
                btnClass: 'btn-pill',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                disabled: true,
                btnClass: 'btn-pill',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                disabled: true,
                btnClass: 'btn-pill',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                disabled: true,
                btnClass: 'btn-pill',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                disabled: true,
                btnClass: 'btn-pill',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                disabled: true,
                btnClass: 'btn-pill',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: OutlineButtons,
        span: Add,
        code1: `.btn-pill & .btn-outline-*`,
        detail1: 'class for button with outline',
        btnSub: [
            {
                btnClass: 'btn-pill',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: OutlineLargeButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for outline and',
        code2: '.btn-lg',
        detail2: 'class for large button',
        cardId: 'outline-bold-button',
        btnSub: [
            {
                btnClass: 'btn-pill',
                size: 'lg',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'lg',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'lg',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'lg',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'lg',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'lg',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'lg',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: OutlineSmallButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for outline and',
        code2: '.btn-sm',
        detail2: 'class for small button',
        cardId: 'outline-small-button',
        btnSub: [
            {
                btnClass: 'btn-pill',
                size: 'sm',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'sm',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'sm',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'sm',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'sm',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'sm',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'sm',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: OutlineExtraSmallButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for outline and',
        code2: '.btn-xs',
        detail2: 'class for extra small button',
        cardId: 'ex-outline-small-button',
        btnSub: [
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: DisabledOutlineButtons,
        span: Add,
        code1: `.disabled`,
        detail1: 'class or',
        code2: `disabled='disabled'}`,
        detail2: 'attribute for disabled state',
        cardId: 'ex-outline-small-button',
        btnSub: [
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: GradienButtons,
        span: Add,
        code1: `.btn-*-gradien`,
        detail1: 'class for gradien button',
        cardId: 'gradiant',
        btnSub: [
            {
                btnClass: 'btn-pill',
                colorClass: 'primary-gradien',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill',
                colorClass: 'secondary-gradien',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill',
                colorClass: 'success-gradien',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill',
                colorClass: 'info-gradien',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill',
                colorClass: 'warning-gradien',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill',
                colorClass: 'danger-gradien',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill',
                colorClass: 'light-gradien',
                title: LightButton,
            }
        ]
    },
]

export const FlatButtonData = [
    {
        title: DefaultButtons,
        span: 'Add',
        code: `.btn-square`,
        detail: 'class for edge button',
        btnSub: [
            {
                btnClass: 'btn-square',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-square',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-square',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-square',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-square',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-square',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-square',
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: LargeButtons,
        span: 'Add',
        code: `.btn-square & .btn-lg`,
        detail: 'class for large button',
        btnSub: [
            {
                size: 'lg',
                btnClass: 'btn-square',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-square',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-square',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-square',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-square',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-square',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-square',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: SmallButtons,
        span: 'Add',
        code: `.btn-square & .btn-sm`,
        detail: 'class for small button',
        btnSub: [
            {
                size: 'sm',
                btnClass: 'btn-square',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-square',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-square',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-square',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-square',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-square',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-square',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: ExtraSmallButtons,
        span: 'Add',
        code: `.btn-square & .btn-xs`,
        detail: 'class for extra small button',
        btnSub: [
            {
                size: 'xs',
                btnClass: 'btn-square',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-square',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-square',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-square',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-square',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-square',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-square',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: ActiveButtons,
        span: 'Add',
        code: `.active`,
        detail: 'for active state',
        btnSub: [
            {
                active: true,
                btnClass: 'btn-square',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                active: true,
                btnClass: 'btn-square',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                active: true,
                btnClass: 'btn-square',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                active: true,
                btnClass: 'btn-square',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                active: true,
                btnClass: 'btn-square',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                active: true,
                btnClass: 'btn-square',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                active: true,
                btnClass: 'btn-square',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: DisabledButtons,
        span: 'Add',
        code: `.disabled || disabled='disabled'`,
        detail: 'attribute for disabled button',
        btnSub: [
            {
                disabled: true,
                btnClass: 'btn-square',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                disabled: true,
                btnClass: 'btn-square',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                disabled: true,
                btnClass: 'btn-square',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                disabled: true,
                btnClass: 'btn-square',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                disabled: true,
                btnClass: 'btn-square',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                disabled: true,
                btnClass: 'btn-square',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                disabled: true,
                btnClass: 'btn-square',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: OutlineButtons,
        span: Add,
        code1: `.btn-square & .btn-outline-*`,
        detail1: 'class for button with outline',
        btnSub: [
            {
                btnClass: 'btn-square',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-square',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-square',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-square',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-square',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-square',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-square',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: OutlineLargeButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for outline and',
        code2: '.btn-lg',
        detail2: 'class for large button',
        cardId: 'outline-bold-button',
        btnSub: [
            {
                btnClass: 'btn-square',
                size: 'lg',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-square',
                size: 'lg',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-square',
                size: 'lg',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-square',
                size: 'lg',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-square',
                size: 'lg',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-square',
                size: 'lg',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-square',
                size: 'lg',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: OutlineSmallButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for outline and',
        code2: '.btn-sm',
        detail2: 'class for small button',
        cardId: 'outline-small-button',
        btnSub: [
            {
                btnClass: 'btn-square',
                size: 'sm',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-square',
                size: 'sm',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-square',
                size: 'sm',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-square',
                size: 'sm',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-square',
                size: 'sm',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-square',
                size: 'sm',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-square',
                size: 'sm',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: OutlineExtraSmallButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for outline and',
        code2: '.btn-xs',
        detail2: 'class for extra small button',
        cardId: 'ex-outline-small-button',
        btnSub: [
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: DisabledOutlineButtons,
        span: Add,
        code1: `.disabled`,
        detail1: 'class or',
        code2: `disabled='disabled'}`,
        detail2: 'attribute for disabled state',
        cardId: 'ex-outline-small-button',
        btnSub: [
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-square',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: GradienButtons,
        span: Add,
        code1: `.btn-*-gradien`,
        detail1: 'class for gradien button',
        cardId: 'gradiant',
        btnSub: [
            {
                btnClass: 'btn-square',
                colorClass: 'primary-gradien',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-square',
                colorClass: 'secondary-gradien',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-square',
                colorClass: 'success-gradien',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-square',
                colorClass: 'info-gradien',
                title: InfoButton,
            },
            {
                btnClass: 'btn-square',
                colorClass: 'warning-gradien',
                title: WarningButton,
            },
            {
                btnClass: 'btn-square',
                colorClass: 'danger-gradien',
                title: DangerButton,
            },
            {
                btnClass: 'btn-square',
                colorClass: 'light-gradien',
                title: LightButton,
            }
        ]
    },
]

export const GroupBtnData = [
    {
        title: BasicButtonGroup,
        color: [
            {
                colorClass: 'primary',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                colorClass: 'secondary',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                colorClass: 'success',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                colorClass: 'info',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                colorClass: 'warning',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                colorClass: 'danger',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                colorClass: 'light',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                colClass: 'Button-group-mb-sm',
                colorClass: 'dark',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            }
        ]
    },
    {
        title: EdgesButtonGroup,
        color: [
            {
                btnClass: 'btn-group-pill',
                colorClass: 'primary',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-pill',
                colorClass: 'secondary',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-pill',
                colorClass: 'success',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-pill',
                colorClass: 'info',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-pill',
                colorClass: 'warning',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-pill',
                colorClass: 'danger',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-pill',
                colorClass: 'light',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-pill',
                colClass: 'Button-group-mb-sm',
                colorClass: 'dark',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            }
        ]
    },
    {
        title: FlatButtonGroup,
        color: [
            {
                btnClass: 'btn-group-square',
                colorClass: 'primary',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-square',
                colorClass: 'secondary',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-square',
                colorClass: 'success',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-square',
                colorClass: 'info',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-square',
                colorClass: 'warning',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-square',
                colorClass: 'danger',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-square',
                colorClass: 'light',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                btnClass: 'btn-group-square',
                colClass: 'button-group-mb-sm xl-50',
                colorClass: 'dark',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            }
        ]
    },
    {
        title: LargeButtonGroup,
        color: [
            {
                size: 'lg',
                colorClass: 'primary',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colorClass: 'secondary',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colorClass: 'success',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colorClass: 'info',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colorClass: 'warning',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colorClass: 'danger',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colorClass: 'light',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colClass: 'button-group-mb-sm xl-50',
                colorClass: 'dark',
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            }
        ]
    },
    {
        title: LargeEdgesButtonGroup,
        color: [
            {
                size: 'lg',
                colorClass: 'primary',
                btnClass: "btn-group-pill",
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colorClass: 'secondary',
                btnClass: "btn-group-pill",
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colorClass: 'success',
                btnClass: "btn-group-pill",
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colorClass: 'info',
                btnClass: "btn-group-pill",
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colorClass: 'warning',
                btnClass: "btn-group-pill",
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colorClass: 'danger',
                btnClass: "btn-group-pill",
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colorClass: 'light',
                btnClass: "btn-group-pill",
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            },
            {
                size: 'lg',
                colClass: 'button-group-mb-sm xl-50',
                colorClass: 'dark',
                btnClass: "btn-group-pill",
                title1: 'Left',
                title2: 'Middle',
                title3: 'Right'
            }
        ]
    },
    {
        title: OutlineCustomButtonGroup,
        color: [
            {
                size: 'lg',
                colorClass: 'primary',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: false,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'secondary',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: false,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'success',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: false,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'info',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: false,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'warning',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: false,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'danger',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: false,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'light',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: false,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colClass: 'button-group-mb-sm xl-50',
                colorClass: 'dark',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: false,
                title3: 'Right',
                outline3: true
            }
        ]
    },
    {
        title: OutlineCustomButtonGroup,
        color: [
            {
                size: 'lg',
                colorClass: 'primary',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: false,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: false
            },
            {
                size: 'lg',
                colorClass: 'secondary',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: false,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: false
            },
            {
                size: 'lg',
                colorClass: 'success',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: false,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: false
            },
            {
                size: 'lg',
                colorClass: 'info',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: false,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: false
            },
            {
                size: 'lg',
                colorClass: 'warning',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: false,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: false
            },
            {
                size: 'lg',
                colorClass: 'danger',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: false,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: false
            },
            {
                size: 'lg',
                colorClass: 'light',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: false,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: false
            },
            {
                size: 'lg',
                colClass: 'button-group-mb-sm xl-50',
                colorClass: 'dark',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: false,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: false
            }
        ]
    },
    {
        title: OutlineButtonGroup,
        color: [
            {
                size: 'lg',
                colorClass: 'primary',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'secondary',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'success',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'info',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'warning',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'danger',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'light',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colClass: 'button-group-mb-sm xl-50',
                colorClass: 'dark',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            }
        ]
    },
    {
        title: OutlineEdgesButton,
        color: [
            {
                size: 'lg',
                colorClass: 'primary',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'secondary',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'success',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'info',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'warning',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'danger',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'light',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colClass: 'button-group-mb-sm xl-50',
                colorClass: 'dark',
                btnClass: "btn-group-pill",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            }
        ]
    },
    {
        title: OutlineFlatButton,
        color: [
            {
                size: 'lg',
                colorClass: 'primary',
                btnClass: "btn-group-square",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'secondary',
                btnClass: "btn-group-square",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'success',
                btnClass: "btn-group-square",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'info',
                btnClass: "btn-group-square",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'warning',
                btnClass: "btn-group-square",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'danger',
                btnClass: "btn-group-square",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colorClass: 'light',
                btnClass: "btn-group-square",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            },
            {
                size: 'lg',
                colClass: 'button-group-mb-sm xl-50',
                colorClass: 'dark',
                btnClass: "btn-group-square",
                title1: 'Left',
                outline1: true,
                title2: 'Middle',
                outline2: true,
                title3: 'Right',
                outline3: true
            }
        ]
    },
]

export const RadioBtnData = [
    {
        title: RadioButtonGroup,
        span: Add,
        code1: '.active',
        detail1: 'for active state and',
        code2: '.disabled',
        detail2: 'class or',
        code3: `disabled='disabled'`,
        detail3: 'attribute',
        btnSub: [
            {
                btnClass: 'btn-radio',
                colorClass: 'primary',
                divClass: 'radio radio-primary',
                id1: 'radio7',
                title1: 'Option 1',
                id2: 'radio8',
                title2: 'Option 2',
            },
            {
                btnClass: 'btn-radio',
                colorClass: 'secondary',
                divClass: 'radio radio-secondary',
                id1: 'radio11',
                title1: 'Option 1',
                id2: 'radio12',
                title2: 'Option 2',
            },
            {
                btnClass: 'btn-radio',
                colorClass: 'success',
                divClass: 'radio radio-success',
                id1: 'radio13',
                title1: 'Option 1',
                id2: 'radio14',
                title2: 'Option 2',
            },
            {
                btnClass: 'btn-radio',
                colorClass: 'info',
                divClass: 'radio radio-info',
                id1: 'radio15',
                title1: 'Option 1',
                id2: 'radio16',
                title2: 'Option 2',
            },
            {
                btnClass: 'btn-radio',
                colorClass: 'warning',
                divClass: 'radio radio-warning',
                id1: 'radio17',
                title1: 'Option 1',
                id2: 'radio18',
                title2: 'Option 2',
            },
            {
                btnClass: 'btn-radio',
                colorClass: 'danger',
                divClass: 'radio radio-danger',
                id1: 'radio20',
                title1: 'Option 1',
                id2: 'radio22',
                title2: 'Option 2',
            },
            {
                colClass: 'button-group-mb-sm xl-50',
                btnClass: 'btn-radio',
                colorClass: 'light txt-dark',
                divClass: 'radio radio-light',
                id1: 'radio23',
                title1: 'Option 1',
                id2: 'radio24',
                title2: 'Option 2',
            }
        ]
    },
    {
        title: CheckBoxButtonGroup,
        span: Add,
        code1: '.active',
        detail1: 'for active state and',
        code2: '.disabled',
        detail2: 'class or',
        code3: `disabled='disabled'`,
        detail3: 'attribute',
        btnSub: [
            {
                btnClass: 'btn-option',
                colorClass: 'primary',
                divClass: 'checkbox checkbox-primary',
                id1: 'checkbox-primary-1',
                title1: 'Option 1',
                id2: 'checkbox-primary-2',
                title2: 'Option 2',
                checkBox: true
            },
            {
                btnClass: 'btn-group btn-option',
                colorClass: 'secondary',
                divClass: 'checkbox checkbox-secondary',
                id1: 'checkbox-primary-3',
                title1: 'Option 1',
                id2: 'checkbox-primary-4',
                title2: 'Option 2',
                checkBox: true
            },
            {
                btnClass: 'btn-group btn-option',
                colorClass: 'success',
                divClass: 'checkbox checkbox-success',
                id1: 'checkbox-primary-5',
                title1: 'Option 1',
                id2: 'checkbox-primary-6',
                title2: 'Option 2',
                checkBox: true
            },
            {
                btnClass: 'btn-group btn-option',
                colorClass: 'info',
                divClass: 'checkbox checkbox-info',
                id1: 'checkbox-primary-7',
                title1: 'Option 1',
                id2: 'checkbox-primary-8',
                title2: 'Option 2',
                checkBox: true
            },
            {
                btnClass: 'btn-group btn-option',
                colorClass: 'warning',
                divClass: 'checkbox checkbox-warning',
                id1: 'checkbox-primary-9',
                title1: 'Option 1',
                id2: 'checkbox-primary-10',
                title2: 'Option 2',
                checkBox: true
            },
            {
                btnClass: 'btn-group btn-option',
                colorClass: 'danger',
                divClass: 'checkbox checkbox-danger',
                id1: 'checkbox-danger-11',
                title1: 'Option 1',
                id2: 'checkbox-danger-12',
                title2: 'Option 2',
                checkBox: true
            },
            {
                colClass: 'button-group-mb-sm',
                btnClass: 'btn-group btn-option',
                colorClass: 'light txt-dark',
                divClass: 'checkbox checkbox-light',
                id1: 'checkbox-light-13',
                title1: 'Option 1',
                id2: 'checkbox-light-14',
                title2: 'Option 2',
                checkBox: true
            }
        ]
    },
]

export const RaisedButtonData = [
    {
        title: DefaultButtons,
        span: 'Add',
        code: `.btn-pill & .btn-air-*`,
        detail: 'class  for raised button',
        btnSub: [
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: LargeButtons,
        span: 'Add',
        code: `.btn-square & .btn-lg`,
        detail: 'class for large button',
        btnSub: [
            {
                size: 'lg',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'lg',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: SmallButtons,
        span: 'Add',
        code: `.btn-square & .btn-sm`,
        detail: 'class for small button',
        btnSub: [
            {
                size: 'sm',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'sm',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: ExtraSmallButtons,
        span: 'Add',
        code: `.btn-square & .btn-xs`,
        detail: 'class for extra small button',
        btnSub: [
            {
                size: 'xs',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                size: 'xs',
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: ActiveButtons,
        span: 'Add',
        code: `.active`,
        detail: 'for active state',
        btnSub: [
            {
                active: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                active: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                active: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                active: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                active: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                active: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                active: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: DisabledButtons,
        span: 'Add',
        code: `.disabled || disabled='disabled'`,
        detail: 'attribute for disabled button',
        btnSub: [
            {
                disabled: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                disabled: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                disabled: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                disabled: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'info',
                title: InfoButton,
            },
            {
                disabled: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                disabled: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                disabled: true,
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: OutlineButtons,
        span: Add,
        code1: `.btn-square & .btn-outline-*`,
        detail1: 'class for button with outline',
        btnSub: [
            {
                btnClass: 'btn-pill btn-air-primary',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: OutlineLargeButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for outline and',
        code2: '.btn-lg',
        detail2: 'class for large button',
        cardId: 'outline-bold-button',
        btnSub: [
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'lg',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'lg',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'lg',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'lg',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'lg',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'lg',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'lg',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: OutlineSmallButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for outline and',
        code2: '.btn-sm',
        detail2: 'class for small button',
        cardId: 'outline-small-button',
        btnSub: [
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'sm',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'sm',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'sm',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'sm',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'sm',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'sm',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'sm',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: OutlineExtraSmallButtons,
        span: Add,
        code1: `.btn-outline-*`,
        detail1: 'class for outline and',
        code2: '.btn-xs',
        detail2: 'class for extra small button',
        cardId: 'ex-outline-small-button',
        btnSub: [
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                colorClass: 'light',
                title: LightButton,
            }
        ]
    },
    {
        title: DisabledOutlineButtons,
        span: Add,
        code1: `.disabled`,
        detail1: 'class or',
        code2: `disabled='disabled'}`,
        detail2: 'attribute for disabled state',
        cardId: 'ex-outline-small-button',
        btnSub: [
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'primary',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'secondary',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'success',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'info',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'warning',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'danger',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                size: 'xs',
                outline: true,
                disabled: true,
                colorClass: 'light',
                title: LightButton,
            },
        ]
    },
    {
        title: GradienButtons,
        span: Add,
        code1: `.btn-*-gradien`,
        detail1: 'class for gradien button',
        cardId: 'gradiant',
        btnSub: [
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'primary-gradien',
                title: PrimaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'secondary-gradien',
                title: SecondaryButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'success-gradien',
                title: SuccessButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'info-gradien',
                title: InfoButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'warning-gradien',
                title: WarningButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'danger-gradien',
                title: DangerButton,
            },
            {
                btnClass: 'btn-pill btn-air-primary',
                colorClass: 'light-gradien',
                title: LightButton,
            }
        ]
    },
]

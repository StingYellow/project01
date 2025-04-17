from odoo import api, fields, models
from odoo.exceptions import ValidationError

class res_mode(models.Model):
    _name = "res.mode"
    _description = 'Res Mode'


    name=fields.Char(string='Tên')
    user_id = fields.Many2one('res.users', string="User")
    role = fields.Selection([('customer', 'Customer'), ('driver', 'Driver')], string='Role', required=True)
    car_booking_customer_ids = fields.One2many(
        'car.booking',
        'customer_id',
        string='Các đơn đặt xe'
    )

    driver_license = fields.Char(string='Giấy phép lái xe', required=True)
    driver_status = fields.Selection([('online', 'Online'), ('offline', 'Offline')],
                                     default="online",string='Trạng thái hoạt động của tài xế', required=True)
    phone = fields.Char(string='Số điện thoại', required=True)
    email = fields.Char(string='Địa chỉ email')
    address = fields.Char(string='Địa chỉ khách hàng', required=True)

    @api.constrains('phone')
    def _check_unique_and_required_phone(self):
        for rec in self:
            existing = self.search([
                ('phone', '=', rec.phone),
                ('id', '!=', rec.id)
            ], limit=1)
            if existing:
                raise ValidationError("Số điện thoại đã tồn tại trong hệ thống!")


    # 2. Kiểm tra email không trùng và không rỗng
    @api.constrains('email')
    def _check_unique_and_required_email(self):
        for rec in self:
            # Chỉ áp dụng với partner có role
            if rec.email:
                existing = self.search([
                    ('email', '=', rec.email),
                    ('id', '!=', rec.id)
                ], limit=1)
                if existing:
                    raise ValidationError("Email đã tồn tại trong hệ thống!")

    # 3. Tài xế phải có driver_license và không trùng với tài xế khác
    @api.constrains('driver_license', 'role')
    def _check_driver_license_required_and_unique(self):
        for rec in self:
            if rec.role == 'driver':
                if not rec.driver_license:
                    raise ValidationError("Tài xế bắt buộc phải có giấy phép lái xe!")

                existing = self.search([
                    ('driver_license', '=', rec.driver_license),
                    ('id', '!=', rec.id),
                    ('role', '=', 'driver')
                ], limit=1)
                if existing:
                    raise ValidationError("Số giấy phép lái xe đã tồn tại trong hệ thống!")

    # 4. Khách hàng phải có địa chỉ
    @api.constrains('address', 'role')
    def _check_customer_address_required(self):
        for rec in self:
            if rec.role == 'customer' and not rec.address:
                raise ValidationError("Khách hàng bắt buộc phải có địa chỉ!")

    @api.constrains('role')
    def _check_role_change_from_customer(self):
        for partner in self:
            # Lấy giá trị cũ từ bản ghi trước khi thay đổi
            old_role = partner._origin.role if partner._origin else False

            # Kiểm tra khi chuyển từ customer sang driver
            if old_role == 'customer' and partner.role == 'driver':
                active_bookings = self.env['car.booking'].search([
                    ('customer_id', '=', partner.id),
                    ('state', 'not in', ['hoan_thanh', 'huy']),
                ])
                if active_bookings:
                    raise ValidationError(
                        "Không thể chuyển vai trò sang 'driver' vì người này còn đơn đặt xe chưa hoàn thành hoặc chưa hủy."
                    )

            # Kiểm tra khi chuyển từ driver sang vai trò khác
            if old_role == 'driver' and partner.role != 'driver':
                active_driver_bookings = self.env['car.booking'].search([
                    ('driver_id', '=', partner.id),
                    ('state', 'not in', ['hoan_thanh', 'huy']),
                ])
                if active_driver_bookings:
                    raise ValidationError(
                        "Không thể chuyển vai trò từ 'driver' sang '%s' vì người này đang là tài xế trong các đơn chưa hoàn thành hoặc chưa hủy."
                        % partner.role
                    )
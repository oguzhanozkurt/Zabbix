# Zabbix Templates / Zabbix Şablonları

## EN

This repository contains custom **Zabbix templates** maintained by **oguzhanozkurt**.

Templates are organized in a structure similar to the official Zabbix template repository and exported in **YAML** format for easy import and version control.

### Branches (Zabbix versions)

Templates may differ between Zabbix versions. Please use the branch that matches your environment:

- **main**: Repository overview and documentation
- **zabbix-7.0**: Templates tested and maintained for Zabbix 7.0

> If you use another Zabbix version, check the available branches.

### Structure

Templates are grouped by category under the `Templates/` directory (e.g. `san`, `net`, `db`, `os`, etc.):



Each template folder includes:
- `README.md`: Requirements, setup notes, macros, and usage instructions
- `*.yaml`: Zabbix template export file

### How to import

1. Download the template `.yaml` file from the branch you use.
2. In Zabbix UI go to: **Data collection → Templates → Import**
3. Upload the `.yaml` file and complete the import.
4. Link the imported template to the target host.

### Notes

- These templates are provided as-is.
- If you find an issue or want to contribute improvements, feel free to open an Issue or Pull Request.

---

## TR

Bu repo, **oguzhanozkurt** tarafından geliştirilen özel **Zabbix template** (şablon) dosyalarını içerir.

Şablonlar, resmi Zabbix template deposuna benzer bir klasör yapısında tutulur ve kolay import/versiyonlama için **YAML** formatında dışa aktarılmıştır.

### Branch'ler (Zabbix sürümleri)

Zabbix sürümüne göre template içerikleri değişebilir. Kullandığınız Zabbix sürümüne uygun branch'i seçin:

- **main**: Repo genel açıklama ve dokümantasyon
- **zabbix-7.0**: Zabbix 7.0 için test edilmiş ve sürdürülen template’ler

> Farklı bir Zabbix sürümü kullanıyorsanız mevcut branch’leri kontrol edin.

### Klasör yapısı

Template’ler `Templates/` altında kategori bazlı toplanır (örn. `san`, `net`, `db`, `os` vb.):

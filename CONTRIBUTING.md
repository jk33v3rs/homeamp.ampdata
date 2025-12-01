# Contributing Guidelines

Thank you for your interest in contributing to the AMP Server Configuration Repository! This document outlines how to contribute effectively to this project.

## 🚀 Getting Started

### Prerequisites
- Git installed on your local machine
- Basic understanding of Minecraft server administration
- Familiarity with AMP (Application Management Panel)
- Knowledge of relevant technologies (datapacks, plugins, server configs)

### Setting Up Your Development Environment
1. Fork this repository
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/amp-server-config.git
   cd amp-server-config
   ```
3. Create a new branch for your contribution:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Types of Contributions

### 1. Datapack Additions
- **New datapacks**: Add well-tested, popular datapacks
- **Version updates**: Update existing datapacks to newer versions
- **Compatibility fixes**: Fix issues with existing datapacks

#### Datapack Submission Guidelines:
- Include the original download source
- Verify compatibility with current Minecraft versions
- Test in a development environment
- Include brief description of functionality

### 2. Plugin Contributions
- **New plugins**: Add useful server plugins
- **Configuration updates**: Improve existing plugin configs
- **Localization**: Add language support for plugins

#### Plugin Submission Guidelines:
- Only submit plugins from trusted sources
- Include configuration examples
- Document any dependencies
- Test for conflicts with existing plugins

### 3. Configuration Improvements
- **Server optimizations**: Improve performance settings
- **Security enhancements**: Add security-focused configurations
- **Template additions**: New deployment templates

#### Configuration Guidelines:
- Comment your changes clearly
- Test on multiple server types
- Document any breaking changes
- Follow existing file structure

### 4. Documentation Updates
- **README improvements**: Enhance setup instructions
- **Guide additions**: Add new how-to guides
- **Translation**: Translate documentation to other languages

## 🔍 Code Review Process

### Before Submitting
1. **Test thoroughly**: Ensure your changes work as expected
2. **Check compatibility**: Verify compatibility with existing setup
3. **Follow conventions**: Maintain consistent file naming and structure
4. **Document changes**: Update relevant documentation

### Pull Request Guidelines
1. **Clear title**: Use descriptive titles (e.g., "Add Terralith v2.5.11 datapack")
2. **Detailed description**: Explain what you're adding/changing and why
3. **Testing notes**: Include how you tested your changes
4. **Breaking changes**: Clearly mark any breaking changes

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New datapack
- [ ] Plugin addition
- [ ] Configuration update
- [ ] Documentation update
- [ ] Bug fix

## Testing
- [ ] Tested in development environment
- [ ] Verified compatibility with existing setup
- [ ] No conflicts with other components

## Checklist
- [ ] Code follows project conventions
- [ ] Documentation updated
- [ ] No sensitive information included
- [ ] Changelog updated (if applicable)
```

## 📂 File Organization Standards

### Directory Structure
```
datapacksrepo/
├── world-generation/     # World gen datapacks
├── structures/          # Structure modification datapacks
├── gameplay/            # Gameplay enhancement datapacks
└── utility/             # Quality of life datapacks

pluginsrepo/
├── administration/      # Server admin plugins
├── gameplay/           # Player experience plugins
└── utilities/          # Helper/utility plugins

server-configs/
├── templates/          # Configuration templates
└── examples/           # Example configurations
```

### Naming Conventions
- **Datapacks**: `datapack-name-version.zip`
- **Plugins**: `PluginName-version.jar`
- **Configurations**: `service-config.json` or `service-config.yml`

## 🧪 Testing Requirements

### Datapack Testing
- Test in creative and survival modes
- Verify no conflicts with other datapacks
- Check performance impact
- Test on different world types

### Plugin Testing
- Install on clean server instance
- Test core functionality
- Check for error messages in console
- Verify compatibility with other plugins

### Configuration Testing
- Deploy to test server
- Monitor performance metrics
- Check log files for errors
- Validate with different server loads

## 📋 Quality Standards

### Code Quality
- Use consistent formatting
- Include appropriate comments
- Follow security best practices
- Optimize for performance

### Documentation Quality
- Clear, concise instructions
- Include examples where helpful
- Keep information up to date
- Use proper markdown formatting

## 🚫 What Not to Contribute

### Prohibited Content
- Cracked/pirated software
- Malicious code or exploits
- Copyrighted content without permission
- Untested or broken configurations
- Personal server credentials or sensitive data

### Discouraged Content
- Experimental/alpha versions without testing
- Duplicate functionality without improvement
- Overly complex solutions for simple problems
- Platform-specific solutions without documentation

## 🐛 Reporting Issues

### Bug Reports
Use the issue template to report:
- Configuration errors
- Compatibility problems
- Documentation inaccuracies
- Performance issues

### Feature Requests
For new features:
- Explain the use case
- Describe the proposed solution
- Consider implementation complexity
- Discuss potential alternatives

## 📞 Getting Help

### Community Support
- Create an issue for questions
- Check existing issues for similar problems
- Join community discussions

### Development Support
- Review existing code for examples
- Check documentation for guidelines
- Ask for clarification in pull requests

## 🏆 Recognition

Contributors will be recognized through:
- GitHub contributor listings
- Changelog acknowledgments
- Community shout-outs for significant contributions

## 📄 Legal Considerations

### Licensing
- Respect original licenses of contributed content
- Don't contribute content you don't have rights to
- Follow fair use guidelines
- Include proper attribution

### Liability
- Test your contributions thoroughly
- Don't submit known problematic code
- Be responsive to issues with your contributions

---

Thank you for contributing to make this repository a valuable resource for the Minecraft server community!
